import json
import boto3
import cfnresponse

s3 = boto3.client('s3')

def handler(event, context):
    response_status = cfnresponse.SUCCESS
    try:
        if event['RequestType'] == 'Delete':
            bucket_names = event['ResourceProperties']['BucketNames']
            for bucket_name in bucket_names:
                response_status = cleanup_bucket(bucket_name)
                if response_status == cfnresponse.FAILED:
                    break
    except Exception as e:
        print(f"Error: {e}")
        response_status = cfnresponse.FAILED
    
    cfnresponse.send(event, context, response_status, {})

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
        return cfnresponse.SUCCESS
    except Exception as e:
        print(f"Failed to clean up bucket: {e}")
        return cfnresponse.FAILED
