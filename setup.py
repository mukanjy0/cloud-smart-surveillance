import os
import boto3
import cv2
import json
import random
from faker import Faker

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')
rekognition = boto3.client('rekognition')

people_collection_id = os.environ['PEOPLE_COLLECTION']
offenders_collection_id = os.environ['OFFENDERS_COLLECTION']

people_table_name = os.environ['PEOPLE_TABLE']
images_bucket_name = os.environ['IMAGE_CLOUD_STORAGE']

people_table = dynamodb.Table(people_table_name)

def initialize_collection(query_result, collection_id):
    if not query_result['Items']:
        raise Exception(f'Cannot read tenants from table {people_table_name}')

    for obj in query_result['Items']:
        image_url = obj['image_url']
        
        image_id = str(image_url).split(f"{images_bucket_name}/")[-1]

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

def initialize_people_collection():
    query_result = people_table.query(
        ProjectionExpression='image_url'
    )
    initialize_collection(query_result, people_collection_id)

def initialize_offenders_collection():
    query_result = people_table.query(
        FilterExpression=Attr('offender').eq(True),
        ProjectionExpression='image_url'
    )
    initialize_collection(query_result, offenders_collection_id)


def generate_security_staff_data(tenant):
    city = random.choice(cities)
    return {
        'tenant_id': tenant,
        'first_name': faker.first_name(),
        'last_name': faker.last_name(),
        'dni': '7' + ''.join([str(random.randint(0, 9)) for _ in range(7)]),
        'phone': '9' + ''.join([str(random.randint(0, 9)) for _ in range(8)]),
        'email': faker.email(),
        'tenant': tenant,
        'country': 'Peru',
        'city': city
    }

def generate_person_data(image_url, offender):
    city = random.choice(cities)
    return {
        'person_id': faker.uuid4(),
        'name': faker.first_name(),
        'lastname': faker.last_name(),
        'dni': '7' + ''.join([str(random.randint(0, 9)) for _ in range(7)]),
        'phone': '9' + ''.join([str(random.randint(0, 9)) for _ in range(8)]),
        'country': 'Peru',
        'city': city,
        'offender': offender,
        'image_url': image_url
    }

def get_tenant_from_filename(filename):
    filename_lower = filename.lower()
    for tenant in tenants:
        if tenant.lower() in filename_lower:
            return tenant
    return None

def upload_files_to_s3(folder_path, bucket_name, file_extension):
    s3 = boto3.client('s3')
    uploaded_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(file_extension):
                tenant = get_tenant_from_filename(file)
                if tenant:
                    file_path = os.path.join(root, file)
                    s3_key = f'{tenant}/{file}'
                    try:
                        s3.upload_file(file_path, bucket_name, s3_key)
                        uploaded_files.append(s3_key)
                        print(f'Successfully uploaded {file_path} to {bucket_name}/{s3_key}')
                    except Exception as e:
                        print(f'Error uploading {file_path}: {e}')
    return uploaded_files

def get_image_urls(bucket_name):
    s3 = boto3.client('s3')
    result = s3.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in result:
        return [f's3://{bucket_name}/{item["Key"]}' for item in result['Contents']]
    else:
        return []

def lambda_handler(event, context):
    bucket_name_videos = 'smart-surveillance-videos'
    bucket_name_images = 'smart-surveillance-images'
    folder_path_videos = './SimulationVideos'
    folder_path_images = './faces'
    dynamodb = boto3.resource('dynamodb')
    table_name_security = 'SecurityStaff'
    table_name_people = 'People'
    table_name_offenders = 'Offenders'
    table_security = dynamodb.Table(table_name_security)
    table_people = dynamodb.Table(table_name_people)
    table_offenders = dynamodb.Table(table_name_offenders)
    
    tenants = ['UTEC', 'UPC', 'Rimac', 'Interbank']
    cities = ['Lima', 'Cusco', 'Arequipa', 'Trujillo', 'Chiclayo', 'Piura', 'Iquitos', 'Pucallpa']
    faker = Faker()
    Faker.seed(0)

    try:
        initialize_people_collection()
        initialize_offenders_collection()
        for tenant in tenants:
            for _ in range(5):
                staff_data = generate_security_staff_data(tenant)
                table_security.put_item(Item=staff_data)
                print(f'Inserted data for {tenant}: {staff_data}')

        upload_files_to_s3(folder_path_videos, bucket_name_videos, '.mp4')

        upload_files_to_s3(folder_path_images, bucket_name_images, '.jpeg')

        image_urls = get_image_urls(bucket_name_images)

        for i, image_url in enumerate(image_urls):
            offender = (i % 10 == 0)  
            person_data = generate_person_data(image_url, offender)
            table_people.put_item(Item=person_data)
            print(f'Inserted person data: {person_data}')

            if offender:
                table_offenders.put_item(Item=person_data)
                print(f'Inserted offender data: {person_data}')
        
        return {
            'statusCode': 200,
            'body': 'Setup Successfully Completed!'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': 'Error: Setup Failed!'
        }
