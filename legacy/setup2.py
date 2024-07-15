import os
import boto3
import cv2
import json

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')
rekognition = boto3.client('rekognition')

collection_id = 'your-collection-id'  # Replace with your collection ID

people_table_name = os.environ['PEOPLE_TABLE']
images_bucket_name = os.environ['IMAGE_CLOUD_STORAGE']

people_table = dynamodb.Table(people_table_name)

def initialize_collection(query_result, collection_id):
    # Iterate through the list of objects (images) and index faces
    query_result = people_table.query(
        FilterExpression=Attr('offender').eq(True),
        ProjectionExpression='image_url'
    )

    if not query_result['Items']:
        raise Exception(f'Cannot read tenants from table {people_table_name}')

    for obj in query_result['Items']:
        image_url = obj['image_url']
        
        image_id = image_url.split(f"{images_bucket_name}/")[-1]

        try:
            index_response = rekognition.index_faces(
                CollectionId=collection_id,
                Image={
                    'S3Object': {
                        'Bucket': images_bucket_name,
                        'Name': image_id
                    }
                },
                ExternalImageId=os.path.basename(image_id),  # Use the file name as the external image ID
                DetectionAttributes=['ALL']
            )
            
            faces = dict()
            for face_record in index_response['FaceRecords']:
                    faces[face_record['Face']['ExternalImageId']] = {
                        'faceID': face_record['Face']['FaceId'],
                        'Confidence': face_record['Face']['Confidence']
                    }
            return {
                'statusCode': 200,
                'indexedFaces': json.dumps(faces)
                }
                
        except Exception as e:
            print(f'Error indexing faces in {image_url}: {str(e)}')