import os
import boto3

dynamodb = boto3.resource('dynamodb')
security_staff_table_name = os.environ['SECURITY_STAFF_TABLE']

def lambda_handler(event, context):
    security_staff_table = dynamodb.Table(security_staff_table_name)

    response = security_staff_table.scan(
        ProjectionExpression='tenant_id'
    )
    
    partition_keys = [item['tenant_id'] for item in response['Items']]
    
    # Handle pagination if there are more items than the scan limit
    while 'LastEvaluatedKey' in response:
        response = security_staff_table.scan(
            ProjectionExpression='tenant_id',
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        partition_keys.extend(item['tenant_id'] for item in response['Items'])
    
    return {
      'statusCode': 200,
      'tenantIds': partition_keys
    }
