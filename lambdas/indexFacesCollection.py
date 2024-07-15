import os
import json
import boto3

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

def lambda_handler(event, context):
    bucket_name = event['body']['bucket_name']
    prefix = event['body']['prefix']
    collection_id = event['body']['collection_id']

    response =  s3.list_objects(Bucket=bucket_name, Prefix=prefix)

    for image in response['Contents']:
        image_key = image['Key']

        try:
            index_response = rekognition.index_faces(
                CollectionId=collection_id,
                Image={
                    'S3Object': {
                        'Bucket': bucket_name,
                        'Name': image_key
                    }
                },
                ExternalImageId=os.path.basename(image_key),  # Use the file name as the external image ID
                MaxFaces=1,
                DetectionAttributes=['ALL']
            )
            
            faces = dict()
            for face_record in index_response['FaceRecords']:
                face = face_record['Face']
                faces[face['ExternalImageId']] = {
                    'faceID': face['FaceId'],
                    'Confidence': face['Confidence']
                }
            return {
                'statusCode': 200,
                'indexedFaces': json.dumps(faces)
                }
                
        except Exception as e:
            print(f'Error indexing faces in {image_key}: {str(e)}')