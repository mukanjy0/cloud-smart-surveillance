import os
import boto3

dynamodb = boto3.resource('dynamodb')
security_staff_table_name = os.environ['SECURITY_STAFF_TABLE:']

def get_tenant_ids():
    security_staff_table = dynamodb.Table(security_staff_table_name)

    query_result = security_staff_table.query(
        Select='SPECIFIC_ATTRIBUTES',
        ProjectionExpression='tenant_id'
    )

    return {
      'statusCode': 200,
      'tenant_ids': query_result['Items']
    }