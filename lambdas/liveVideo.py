import os
import csv
import boto3
import json

s3 = boto3.client('s3')
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')    

bucket_name = os.environ['BUCKET_NAME']
sns_topic_arn = os.environ['SNS_TOPIC_ARN']

filename = 'frame.csv'

def create_frame_csv(items):
  with open(filename, 'w') as f:
      f.write('tenant_id,n_frames,cur_frame\n') 

  for tenant_id in items:
    with open(filename, 'a') as f:
        f.write(f'{tenant_id},240,0\n')

def update_frame_csv(data):
  with open(filename, 'w') as f:
      f.write('tenant_id,n_frames,cur_frame\n') 

  with open(filename, 'a') as f:
    for row in data:
      tenant_id = row['tenant_id']
      n_frames = row['n_frames']
      cur_frame = row['cur_frame']
      f.write(f'{tenant_id},{n_frames},{cur_frame}\n')

def simulate_stream(tenant_id, stream_metadata):
    try:
      cur_frame = stream_metadata['cur_frame']
      image_key = f'{tenant_id}/{cur_frame}.jpg'

      sns.publish(
          TopicArn=sns_topic_arn,
          Message=json.dumps({
            'bucket_name': bucket_name,
            'image_key': image_key
          }),
      )

      stream_metadata['cur_frame'] = (stream_metadata['cur_frame'] + 1) % stream_metadata['n_frames']

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

    if not os.path.exists(filename):
      create_frame_csv(items)

    csv_data = csv.DictReader(filename)
    data = []
    for row in csv_data:
      row['n_frames'] = int(row['n_frames'])
      row['cur_frame'] = int(row['cur_frame'])
      data.append(row)     

    for tenant_id in items:
      try:
        for row in data:
          if row['tenant_id'] == tenant_id:
             stream_metadata = row
             break
        simulate_stream(tenant_id, stream_metadata)
      except Exception as e:
         print(e)
         return {
            'statusCode': 500,
            'body': f'Error in stream simulation'
         }

    update_frame_csv(data)