import os
import json
import boto3

sns = boto3.client('sns')
rekognition = boto3.client('rekognition')

people_table = os.environ["PEOPLE_TABLE"]
people_collection = os.environ["PEOPLE_COLLECTION"]

sns_topic_arn = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    body = event['body']
    bucket_name = body['bucket_name']
    image_key = body['image_key']
    
    try:
        search_response = rekognition.search_faces_by_image(
            CollectionId=people_collection,
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': image_key
                }
            },
            FaceMatchThreshold=80,
            QualityFilter='AUTO'
        )

        # if any of the matches is an offender
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
