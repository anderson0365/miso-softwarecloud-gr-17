from datetime import datetime
from models.database import session, engine
from models.models import Base, Task
import smtplib, yaml, boto3, json, subprocess, os, time

import logging
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.CRITICAL)

config_path = './config.yml'
with open(r'' + config_path) as file:
    config = yaml.full_load(file)
    UPLOAD_FOLDER = config["aws"]["UPLOAD_FOLDER"]
    DOWNLOAD_FOLDER = config["aws"]["DOWNLOAD_FOLDER"]
    AWS_ACCESS_KEY_ID = config["aws"]["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = config["aws"]["AWS_SECRET_ACCESS_KEY"]
    AWS_SESSION_TOKEN = config["aws"]["AWS_SESSION_TOKEN"]
    BUCKET_NAME = config["aws"]["BUCKET_NAME"]
    SMTP_SERVER_IP = config["smtp"]["SERVER"]
    SMTP_PORT = config["smtp"]["PORT"]
    EMAIL = config["smtp"]["EMAIL"]
    SQS_QUEUE_NAME = config["aws"]["SQS_QUEUE_NAME"]

Base.metadata.create_all(bind=engine)

s3 = boto3.client('s3',

    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token= AWS_SESSION_TOKEN
)

bucket = boto3.resource('s3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token= AWS_SESSION_TOKEN
).Bucket(BUCKET_NAME)

def create_queue(sqs_client, queue_name):
    return sqs_client.create_queue(
        QueueName= queue_name,
        Attributes={
            "DelaySeconds": "0",
            "VisibilityTimeout": "60",  # 60 seconds
        }
    )

def get_queue_url(sqs_client, queue_name):
    return sqs_client.get_queue_url(
        QueueName=queue_name,
    )["QueueUrl"]

def send_message(sqs_client, queue_url, message):
    return sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message)
    )

def receive_message(sqs_client, queue_url):
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10,
    )
    msg_list = response.get("Messages", [])
    if len(msg_list) > 0:
        message = msg_list[0]
        message_body = message["Body"]
        return json.loads(message_body), message['ReceiptHandle']
    else:
        return None, ""

def delete_message(sqs_client, queue_url, receipt_handle):
    return sqs_client.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle,
    )

sqs_client = boto3.client('sqs',
    region_name='us-east-1',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token= AWS_SESSION_TOKEN
)

queue_url = get_queue_url(sqs_client, SQS_QUEUE_NAME)


def log(msg):
    print(f"{datetime.utcnow()} - {msg}")

def new_file_extension(old_file_name, new_format):
    file_name = old_file_name.split(".")[0]
    return f"{file_name}.{new_format}"

def conversion_task2(username, email, task_id):
    task = session.query(Task).get(task_id)
    if task.status == 'uploaded':
        s3.download_file(
                    Filename=task.fileName,
                    Bucket=BUCKET_NAME,
                    Key=f"{username}/{UPLOAD_FOLDER}/{task.fileName}")
        new_file_name = new_file_extension(task.fileName, task.newFormat)

        subprocess.run(['ffmpeg', '-y','-i', task.fileName, new_file_name])

        s3.upload_file(
            Filename=new_file_name,
            Bucket=BUCKET_NAME,
            Key=f"{username}/{DOWNLOAD_FOLDER}/{new_file_name}")
                    
        subprocess.run(['rm', task.fileName, new_file_name])

        task.status = 'processed'
        session.commit()
        start_time = datetime.strptime(task.timeStamp, '%Y-%m-%d %H:%M:%S.%f')
        end_time = datetime.now()
        different = end_time - start_time
        minutes, seconds = divmod(different.days * 86400 + different.seconds, 60)
        with smtplib.SMTP(SMTP_SERVER_IP, SMTP_PORT) as server:
            server.sendmail(EMAIL, email, f"Subect: File conversion complete."+
            f"\n\nFile convertion executed: {task.fileName} -> {task.newFormat}." +
            f"\n\nTiempo transcurrido para procesar tarea: {minutes} min, {seconds} sec")  


if __name__ == "__main__":
    log("The worker has started")
    while True:
        msg, receipt_handle = receive_message(sqs_client, queue_url)
        if msg:
            log(f"Conversion process started -> {msg}")
            conversion_task2(msg["username"], msg["email"], msg["task"])
            delete_message(sqs_client, queue_url, receipt_handle)
            log(f"Conversion process ended.")
        else:
            time.sleep(1)