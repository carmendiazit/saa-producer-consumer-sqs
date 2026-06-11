import boto3
import json
import time
import os

sqs = boto3.resource('sqs')

def lambda_handler(event, context):
    queue_url = os.environ['QUEUE_URL']
    queue = sqs.Queue(queue_url)

    message = {
        "coder_id": event.get('coder_id', '123'),
        "spot_id": event.get('spot_id', '321'),
        "timestamp": event.get('timestamp', round(time.time() * 1000))
    }
    
    print(f"📦 Mensaje a enviar: {message}")  
    response = queue.send_message(MessageBody=json.dumps(message))
    print(f"✅ Enviado a SQS - MessageId: {response['MessageId']}")

    return response