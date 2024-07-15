import os
import boto3

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['PEOPLE_TABLE']
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
  person = event['body']

  response = table.put_item(Item=person)

  return {
      'statusCode': 200,
      'response': response
  }