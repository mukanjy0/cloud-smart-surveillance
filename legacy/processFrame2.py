import boto3
import json
import os

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

security_staff_table = os.environ["SECURITY_STAFF_TABLE"]
offenders_table = os.environ["OFFENDERS_TABLE"]
bucket_name = os.environ["CLOUD_STORAGE"]

def lambda_handler(event, context):
    body = json.loads(event['body'])
    image_url = body['url']
    
    image_id = image_url.split(f"{bucket_name}/")[-1]

    try:
        # Detect faces in the image
        detect_response = rekognition.detect_faces(
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': image_id
                }
            },
            Attributes=['ALL']
        )

        # Check if there are faces
        if not detect_response['FaceDetails']:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'No faces detected in image'})
            }

        face_matches = []
        for face_detail in detect_response['FaceDetails']:
            bounding_box = face_detail['BoundingBox']
            
            # Use the bounding box to search for face matches in the collection
            search_response = rekognition.search_faces_by_image(
                CollectionId=os.environ['OFFENDERS_COLLECTION'],
                Image={
                    'S3Object': {
                        'Bucket': bucket_name,
                        'Name': image_id
                    }
                },
                FaceMatchThreshold=80,
                MaxFaces=1,  
                QualityFilter='AUTO'
            )

            if search_response['FaceMatches']:
                face_matches.extend(search_response['FaceMatches'])

        return {
            'statusCode': 200,
            'body': json.dumps({
                'faceDetails': detect_response['FaceDetails'],
                'faceMatches': face_matches
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
