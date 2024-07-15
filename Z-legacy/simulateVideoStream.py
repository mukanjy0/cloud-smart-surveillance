import os
import cv2
import boto3
import json
import pandas as pd
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

security_staff_table_name = os.environ['SECURITY_STAFF_TABLE:']
simulation_video_bucket_name = os.environ['VIDEO_SIMULATION_STORAGE']
video_storage_bucket_name = os.environ['VIDEO_CLOUD_STORAGE']

local_videos_path = os.environ['LOCAL_VIDEOS_PATH']
local_images_path = os.environ['LOCAL_IMAGES_PATH']

sns_topic_arn = os.environ['SNS_TOPIC_ARN']

def get_tenant_ids():
    security_staff_table = dynamodb.Table(security_staff_table_name)

    query_result = security_staff_table.query(
        Select='SPECIFIC_ATTRIBUTES',
        ProjectionExpression='tenant_id'
    )

    return query_result['Items']

def download_video_from_s3(bucket_name, video_key, local_file_path):
    s3.download_file(bucket_name, video_key, local_file_path)

def update_iteration_file(video_path, tenant_id):
    video_capture = cv2.VideoCapture(video_path)
    
    total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))

    video_capture.release()

    with open('fps.csv', 'a') as f:
        f.write(f'{tenant_id},{total_frames},1\n')

def get_frame(video_path, frame_number):
    video_capture = cv2.VideoCapture(video_path)
    
    if not video_capture.isOpened():
      raise ValueError(f"Error opening video file {video_path}")
    
    video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    success, frame = video_capture.read()
    video_capture.release()
    
    if not success:
      raise ValueError(f"Could not read frame {frame_number}")
    
    return frame

def simulate_stream(video_path, tenant_id, stream_metadata):
    try:
      cur_frame = stream_metadata[stream_metadata['tenant_id'] == tenant_id]['cur_frame']
      frame = get_frame(video_path, cur_frame)
      # cv2.imshow('Frame', frame)
      # cv2.destroyAllWindows()
      image_path = f'{local_images_path}/{tenant_id}/{frame}.jpg'
      cv2.imwrite(image_path, frame)

      formatted_datetime = datetime.now().strftime('%Y-%m-%d/%H-%M-%S')
      image_key = f'{tenant_id}/images/{formatted_datetime}.jpg'

      s3.client_upload_file(image_path, video_storage_bucket_name, image_key)

      sns.publish(
          TopicArn=sns_topic_arn,
          Message=json.dumps({
             'image_key': image_key
          }),
      )

      stream_metadata[stream_metadata['tenant_id'] == tenant_id]['cur_frame'] += 1

    except Exception as e:
       print(e)

def lambda_handler(event, context):
    items = get_tenant_ids()

    if not items:
      print(f'Cannot read tenants from table {security_staff_table_name}')
      return

    if not os.path.exists(local_videos_path):
      os.makedirs(local_videos_path)
      os.chdir(local_videos_path)

      with open('frame.csv', 'a') as f:
          f.write('tenant_id,n_frames,cur_frame') 

      for tenant_id in items:
        video_id = f'{tenant_id}.mp4'
        video_path = f'{local_videos_path}/{video_id}'

        download_video_from_s3(simulation_video_bucket_name, video_id, video_path)
        update_iteration_file(video_path, tenant_id)

    stream_metadata = pd.read_csv('frame.csv')

    for tenant_id in items:
      video_id = f'{tenant_id}.mp4'
      video_path = f'{local_videos_path}/{video_id}'

      simulate_stream(video_path, tenant_id, stream_metadata)
    stream_metadata.to_csv('frame.csv', index=False)