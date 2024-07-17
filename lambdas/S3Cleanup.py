import json
import boto3
import cfnresponse

s3 = boto3.client('s3')

def lambda_handler(event, context):
    response = s3.list_buckets()
    bucket_names = []
    for bucket in response['Buckets']:
        bucket_names.append(bucket["Name"])

    for bucket_name in bucket_names:
        response_status = cleanup_bucket(bucket_name)
    return {
        'statusCode': response_status
    }

def cleanup_bucket(bucket_name):
    try:
        response = s3.list_objects_v2(Bucket=bucket_name)
        while 'Contents' in response:
            objects = [{'Key': obj['Key']} for obj in response['Contents']]
            s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
            if response['IsTruncated']:
                response = s3.list_objects_v2(Bucket=bucket_name, ContinuationToken=response['NextContinuationToken'])
            else:
                break
        return 200
    except Exception as e:
        print(f"Failed to clean up bucket: {e}")
        return 500