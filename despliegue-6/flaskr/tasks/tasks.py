from datetime import datetime
from sys import path
from celery import Celery
import os
from flaskr import config
from flaskr.models.models import Task
from pydub import AudioSegment
from ..models import User
from ..models.database import session, engine
from ..models import Base, User
import subprocess
import smtplib, ssl
import yaml
import boto3

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
    CELERY_BROKER_URL = config["app-config"]["CELERY_BROKER_URL"]
    CELERY_RESULT_BACKEND = config["app-config"]["CELERY_RESULT_BACKEND"]

Base.metadata.create_all(bind=engine)

s3 = boto3.client('s3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token= AWS_SESSION_TOKEN
)

celery_app = Celery(__name__)
celery_app.conf.broker_url = os.environ.get("CELERY_BROKER_URL", CELERY_BROKER_URL)
celery_app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", CELERY_RESULT_BACKEND)

# smtp_context = ssl.create_default_context()

@celery_app.task()
def register_login(user, date):
    with open('log_signin.log', 'a+') as file:
        file.write(f"{user} - login at : {date}\n")

def new_file_extension(old_file_name, new_format):
    file_name = old_file_name.split(".")[0]
    return f"{file_name}.{new_format}"

def get_file_extension(file_name):
    return file_name.split(".")[1].lower()

@celery_app.task()
def conversion_task2(user_id, task_id):
    user = session.query(User).get(user_id)
    task = session.query(Task).get(task_id)
    if task.status == 'uploaded':
        s3.download_file(
                    Filename=task.fileName,
                    Bucket=BUCKET_NAME,
                    Key=f"{user.username}/{UPLOAD_FOLDER}/{task.fileName}")
        new_file_name = new_file_extension(task.fileName, task.newFormat)

        subprocess.run(['ffmpeg', '-y','-i', task.fileName, new_file_name])

        s3.upload_file(
            Filename=new_file_name,
            Bucket=BUCKET_NAME,
            Key=f"{user.username}/{DOWNLOAD_FOLDER}/{new_file_name}")
                    
        subprocess.run(['rm', task.fileName, new_file_name])

        task.status = 'processed'
        session.commit()
        start_time = datetime.strptime(task.timeStamp, '%Y-%m-%d %H:%M:%S.%f')
        end_time = datetime.now()
        different = end_time - start_time
        minutes, seconds = divmod(different.days * 86400 + different.seconds, 60)
        with smtplib.SMTP(SMTP_SERVER_IP, SMTP_PORT) as server:
            server.sendmail(EMAIL, user.email, f"Subect: File conversion complete."+
            f"\n\nFile convertion executed: {task.fileName} -> {task.newFormat}." +
            f"\n\nTiempo transcurrido para procesar tarea: {minutes} min, {seconds} sec")  
