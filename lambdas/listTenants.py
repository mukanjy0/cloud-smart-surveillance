import os
import boto3

dynamodb = boto3.resource('dynamodb')
security_staff_table_name = os.environ['SECURITY_STAFF_TABLE']

def lambda_handler(event, context):
    security_staff_table = dynamodb.Table(security_staff_table_name)

    response = security_staff_table.scan(
        ProjectionExpression='tenant_id'
    )
    
    partition_keys = set()
    for item in response['Items']:
        partition_keys.add(item['tenant_id'])
    
    # Handle pagination if there are more items than the scan limit
    while 'LastEvaluatedKey' in response:
        response = security_staff_table.scan(
            ProjectionExpression='tenant_id',
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        for item in response['Items']:
            partition_keys.add(item['tenant_id'])
    
    return {
      'statusCode': 200,
      'tenantIds': list(partition_keys)
    }
