import json
import boto3

# Boto3 - DynamoDB Client - Mode Info: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html
sqs = boto3.resource('sqs')
dynamodb = boto3.resource('dynamodb')

# AWS Lambda Function that consumes event from Queue and writes at DynamoDB
def lambda_handler(event, context):
    if 'Records' in event:
        for record in event['Records']:
            payload = json.loads(record["body"])
            
            # ✅ Estos prints aparecen en CloudWatch Logs
            print(f"📨 Mensaje recibido - CoderID: {payload['coder_id']}")
            print(f"📍 SpotID: {payload['spot_id']}")
            print(f"🕐 Timestamp: {payload['timestamp']}")
            print(f"📦 SQS MessageId: {record['messageId']}")            
            
            if 'coder_id' not in payload:
                raise ValueError('erro format')
            else:
                table = dynamodb.Table('checkinData')
                table.put_item(
                   Item={
                        'coderId': payload['coder_id'],
                        'timestamp': payload['timestamp'],
                        'spotID': payload['spot_id']
                        }
                )

    return {
        'statusCode': 200,
        'body': json.dumps(payload)
    }