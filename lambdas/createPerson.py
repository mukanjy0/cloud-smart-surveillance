import os
import boto3

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['PEOPLE_TABLE']
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
  people = event['body']

  responses = []
  for person in people:
    response = table.put_item(Item=person)
    responses.append(response)

  return {
      'statusCode': 200,
      'responses': responses
  }