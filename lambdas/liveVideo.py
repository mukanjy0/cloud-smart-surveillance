import os
import boto3
import json
import pandas as pd
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')    

bucket_name = os.environ['BUCKET_NAME']
sns_topic_arn = os.environ['SNS_TOPIC_ARN']

def create_frame_csv(items):
  with open('frame.csv', 'w') as f:
      f.write('tenant_id,n_frames,cur_frame') 

  for tenant_id in items:
    with open('fps.csv', 'a') as f:
        f.write(f'{tenant_id},240,0\n')

def simulate_stream(tenant_id, stream_metadata):
    try:
      cur_frame = stream_metadata[stream_metadata['tenant_id'] == tenant_id]['cur_frame']
      image_key = f'{tenant_id}/{cur_frame}.jpg'

      sns.publish(
          TopicArn=sns_topic_arn,
          Message=json.dumps({
            'bucket_name': bucket_name,
            'image_key': image_key
          }),
      )

      n_frames = stream_metadata[stream_metadata['tenant_id'] == tenant_id]['n_frames']
      stream_metadata[stream_metadata['tenant_id'] == tenant_id]['cur_frame'] += 1
      stream_metadata[stream_metadata['tenant_id'] == tenant_id]['cur_frame'] %= n_frames

    except:
      raise Exception

def lambda_handler(event, context):
    invoke_response = lambda_client.invoke(FunctionName="listTenants",
                                           InvocationType='RequestResponse',
                                           )
    response = json.loads(invoke_response['Payload'].read())
    print(response)

    if response['statusCode'] != 200:
        return response

    items = response['tenantIds']

    if not os.path.exists('frame.csv'):
      create_frame_csv(items)

    stream_metadata = pd.read_csv('frame.csv')

    for tenant_id in items:
      try:
        simulate_stream(tenant_id, stream_metadata)
      except Exception as e:
         print(e)
         return {
            'statusCode': 500,
            'body': f'Error in stream simulation'
         }

    stream_metadata.to_csv('frame.csv', index=False)