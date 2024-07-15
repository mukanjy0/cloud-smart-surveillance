import os
import json
import boto3

sns = boto3.client('sns')
rekognition = boto3.client('rekognition')

people_table = os.environ["PEOPLE_TABLE"]
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
        
        bucket_name = message_data['bucket_name']
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

            face_matches.extend(search_response['FaceMatches'])

            # if any of the matches is an offender
            sns.publish(
                TopicArn=sns_topic_arn
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
