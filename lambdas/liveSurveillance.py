import os
import json
import uuid
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

sns = boto3.client('sns')
rekognition = boto3.client('rekognition')

dynamodb = boto3.resource('dynamodb')

recorded_table_name = os.environ["RECORDED_PEOPLE_TABLE"]
recorded_table = dynamodb.Table('RecordedPeople')

people_table_name = os.environ["PEOPLE_TABLE"]
people_table = dynamodb.Table(people_table_name)

people_collection = os.environ["PEOPLE_COLLECTION"]

sns_topic_arn = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    print(event)

    face_matches = []
    for record in event['Records']:
        sqs_message_body = record['body']
        sqs_message_json = json.loads(sqs_message_body)
        sns_message = sqs_message_json['Message']
      
        print(f"Received SNS message: {sns_message}")
      
        try:
            message_data = json.loads(sns_message)
            print(message_data)
            
            bucket_name = message_data['bucket_name']
            image_key = message_data['image_key']
            tenant_id = message_data['tenant_id']
            datetime = message_data['datetime']
            location = message_data['location']
            image_key = message_data['image_key']

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

                print(search_response)

                if search_response['FaceMatches']:
                    face_matches.extend(search_response['FaceMatches'])

                    for match in search_response['FaceMatches']:
                        dni = match['Face']['ExternalImageId']
                        record_id = str(uuid.uuid1())
                        (lat, lon) = location
                        lat = Decimal(str(lat))
                        lon = Decimal(str(lon))

                        record = {
                            'tenant_id': tenant_id,
                            'record_id': record_id,
                            'dni': dni,
                            'datetime': datetime,
                            'latitude': lat,
                            'longitude': lon,
                            'image_key': image_key
                        }

                        response = recorded_table.put_item(Item=record)
                        print(f'Insert on RecordedPeople: {response}')

                        result = people_table.query(
                            FilterExpression=Attr('offender').eq(True) & Attr('dni').eq(dni),
                            KeyConditionExpression=Key('tenant_id').eq(tenant_id)
                        )
                        print(f'Validate if offender: {result}')

                        if result['Items']:
                            person = result['Items'][0]

                            sns.publish(
                                TopicArn=sns_topic_arn,
                                Message=json.dumps({
                                    'tenant_id': tenant_id,
                                    'dni': dni,
                                    'name': person['name'],
                                    'lastname': person['lastname'],
                                    'country': person['country'],
                                    'datetime': datetime,
                                    'location': location,
                                }),
                                MessageAttributes={
                                    'tenant_id': {
                                        'DataType': 'String',
                                        'StringValue': tenant_id
                                    },
                                }
                            )

            except Exception as e:
                print(json.dumps({'error': str(e)}))

        except json.JSONDecodeError:
            print("Received message is not in JSON format")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'faceDetails': face_matches
        })
    }
