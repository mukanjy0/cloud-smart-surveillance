import os
import csv
import boto3
import json
import random
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')    

bucket_name = os.environ['BUCKET_NAME']
list_tenants_function=os.environ['LIST_TENANTS_FUNCTION']
sns_topic_arn = os.environ['SNS_TOPIC_ARN']

file_key = 'frame.csv'
temp_file = f'/tmp/{file_key}'

locations = [
  [40.712776, -74.005974], # Nueva York
  [51.507351, -0.127758], # Londres
  [35.689487, 139.691711], # Tokio
  [-33.868820, 151.209290], # Sídney
  [48.856613, 2.352222], # París
  [34.052235, -118.243683], # Los Ángeles
  [-37.813629, 144.963058] # Melbourne
]


def check_file_exists(bucket_name, file_key):
    try:
        s3.head_object(Bucket=bucket_name, Key=file_key)
        return True
    except Exception as e:
        return False

def create_frame_csv(items):
  with open(temp_file, 'w') as f:
      f.write('tenant_id,n_frames,cur_frame\n') 

  for tenant_id in items:
    with open(temp_file, 'a') as f:
        f.write(f'{tenant_id},240,0\n')
  try:
    response = s3.upload_file(temp_file, bucket_name, file_key)
    print(response)
  except Exception as e:
    print(f'Error uploading file: {e}')
        

def update_frame_csv(data):
  with open(temp_file, 'w') as f:
      f.write('tenant_id,n_frames,cur_frame\n') 

  with open(temp_file, 'a') as f:
    for row in data:
      tenant_id = row['tenant_id']
      n_frames = row['n_frames']
      cur_frame = row['cur_frame']
      f.write(f'{tenant_id},{n_frames},{cur_frame}\n')

  try:
    response = s3.upload_file(temp_file, bucket_name, file_key)
    print(response)
  except Exception as e:
    print(f'Error uploading file: {e}')

def simulate_stream(tenant_id, stream_metadata):
    try:
      for i in range(10):
        cur_frame = stream_metadata['cur_frame']
        image_key = f'{tenant_id}/{cur_frame}.jpg'

        formatted_datetime = datetime.now().strftime('%Y-%m-%d/%H-%M-%S')

        idx = random.randint(0, 6)
        [lat, lon] = locations[idx]

        response = sns.publish(
            TopicArn=sns_topic_arn,
            Message=json.dumps({
              'bucket_name': bucket_name,
              'image_key': image_key,
              'tenant_id': tenant_id,
              'datetime': formatted_datetime,
              'latitude': lat,
              'longitude': lon,
              'image_key': image_key
            }),
        )

        print(f'SNS: {response}')

        stream_metadata['cur_frame'] = (stream_metadata['cur_frame'] + 1) % stream_metadata['n_frames']

    except:
      raise Exception

def lambda_handler(event, context):
    invoke_response = lambda_client.invoke(FunctionName=list_tenants_function,
                                           InvocationType='RequestResponse',
                                           )
    response = json.loads(invoke_response['Payload'].read())
    print(response)

    if response['statusCode'] != 200:
        return response

    items = response['tenantIds']

    if not check_file_exists(bucket_name, file_key):
      create_frame_csv(items)
    else:
      s3.download_file(bucket_name, file_key, temp_file)


    data = []
    with open(temp_file, 'r') as f:
      csv_data = csv.DictReader(f)

      for row in csv_data:
        row['n_frames'] = int(row['n_frames'])
        row['cur_frame'] = int(row['cur_frame'])
        data.append(row)     

    print(f'Data = {data}')
    try:
      for row in data:
        simulate_stream(row['tenant_id'], row)
    except Exception as e:
        print(f'Error in stream simulation: {e}')
        return {
          'statusCode': 500,
          'body': f'Error in stream simulation: {e}'
        }

    update_frame_csv(data)

    if os.path.exists(temp_file):
       os.remove(temp_file)