import json
import boto3

rekognition = boto3.client('rekognition')

def lambda_handler(event, context):
    body = event['body']
    bucket_name = body['bucket_name']
    image_key = body['image_key']
    collection_id = body['collection_id']
    
    try:
        search_response = rekognition.search_faces_by_image(
            CollectionId=collection_id,
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
