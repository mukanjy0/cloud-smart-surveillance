import os
import boto3

dynamodb = boto3.resource('dynamodb')
security_staff_table_name = os.environ['SECURITY_STAFF_TABLE']

def lambda_handler(event, context):
    security_staff_table = dynamodb.Table(security_staff_table_name)

    query_result = security_staff_table.query(
        Select='SPECIFIC_ATTRIBUTES',
        ProjectionExpression='tenant_id'
    )

    return {
      'statusCode': 200,
      'tenantIds': query_result['Items']
    }
