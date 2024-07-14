import os
import json
import boto3

s3 = boto3.client('s3')
sns = boto3.client('sns')
rekognition = boto3.client('rekognition')

security_staff_table = os.environ["SECURITY_STAFF_TABLE"]
offenders_table = os.environ["OFFENDERS_TABLE"]
offenders_collection = os.environ["OFFENDERS_COLLECTION"]
bucket_name = os.environ["CLOUD_STORAGE"]

sns_topic_arn = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    body = json.loads(event['body'])
    image_key = body['image_key']
    
    try:
        search_response = rekognition.search_faces_by_image(
            CollectionId=offenders_collection,
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': image_key
                }
            },
            FaceMatchThreshold=80,
            MaxFaces=1,  
            QualityFilter='AUTO'
        )

        sns.publish(
            TopicArn=sns_topic_arn,
            Message=json.dumps({
                'FaceMatches': search_response['FaceMatches']
            }),
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'faceDetails': search_response['FaceMatches']
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
