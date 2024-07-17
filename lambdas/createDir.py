import boto3

def lambda_handler(event, context):
    bucket_name = event['body']['bucket_name']
    key = event['body']['key'] + '/'
    
    # Proceso    
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    k = bucket.put_object(Key=key)

    return {
        'statusCode': 200,
        'path': bucket_name + '/' + key
    }
