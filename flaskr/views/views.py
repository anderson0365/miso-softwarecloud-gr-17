from re import A
from flask import request, Response
from ..models.database import  session, engine
from ..models import Base, User, Task, TaskSchema
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from ..config import BUCKET_NAME, UPLOAD_FOLDER, DOWNLOAD_FOLDER
from ..tasks import bucket, s3, sqs_client, queue_url, send_message
from werkzeug.utils import secure_filename

Base.metadata.create_all(bind=engine)

task_schema = TaskSchema()

AUDIO_ALLOWED_EXTENSIONS = {'mp3', 'acc', 'ogg', 'wav', 'wma'}


def get_file_extension(filename):
    return filename.split('.')[1].lower()

def remove_extension(filename):
    return filename.split('.')[0]


def allowed_conversions(newFormat, ALLOWED_EXTENSIONS):
    return newFormat in ALLOWED_EXTENSIONS

def get_user(id_user):
    return session.query(User).filter_by(id=id_user).first()

def get_user_task(id_user, id_task):
    user = get_user(id_user)
    if not user:
        return None, None

    task = next((task for task in user.tasks if task.id == id_task), None)
    if task:
        return user, task
    
    return user, None

def new_file_extension(old_file_name, new_format):
    file_name = old_file_name.split(".")[0]
    return f"{file_name}.{new_format}"


def remove_file(base_dir, file):
    s3.delete_object(Bucket=BUCKET_NAME,
                      Key=f"{base_dir}/{file}")


def remove_all_related_files(username, file_name, new_format):
    remove_file(f"{username}/{UPLOAD_FOLDER}", file_name)
    remove_file(f"{username}/{DOWNLOAD_FOLDER}", new_file_extension(file_name, new_format))


def remove_user_dir(username):
    bucket.objects.filter(Prefix=f"{username}/").delete()

def get_file(key):
    return s3.get_object(Bucket=BUCKET_NAME, Key=key)

class ViewSignUp(Resource):
    def post(self):
        if request.json["password1"] == request.json["password2"]:
            new_user = User(
                username=secure_filename(request.json["username"]), email=request.json["email"], password=request.json["password1"])
            try:
                session.add(new_user)
                session.commit()
            except IntegrityError as err:
                session.rollback()
                return 'The given email is already in use.', 404
            except:
                return 'Some of the given parameters are not valid.', 404
            else:
                return {"message": "User created", "New User": new_user.simplified()}
        return 'The given passwords are not equals.', 404


class ViewLogIn(Resource):
    def post(self):
        if 'username' in request.json:
            user = session.query(User).filter_by(username=request.json["username"], password=request.json["password"]).first()
        elif 'email' in request.json:
            user = session.query(User).filter_by(email=request.json["email"], password=request.json["password"]).first()
        
        if not user:
            return "The given user does not exist", 404
        else:
            token = create_access_token(identity=user.id)
            # register_login.delay(user.username, datetime.utcnow())
            return {"message": "Session successful started", "token": token}


class ViewTasks(Resource):

    @jwt_required()
    def get(self):
        user = get_user(get_jwt_identity())
        if not user:
            return "User not found", 404

        tasks = user.tasks
        reverse = False
        if request.json:
            if 'order' in request.json:
                reverse = request.json['order'] == 1

        tasks.sort(key=lambda x: x.id, reverse=reverse)

        if request.json:
            if 'max' in request.json:
                tasks = tasks[:request.json['max']]

        return [task_schema.dump(task) for task in tasks]

    @jwt_required()
    def post(self):
        user = get_user(get_jwt_identity())
        if not user:
            return "User not found", 404

        if 'fileName' not in request.files:
            return "No file part", 404

        file = request.files['fileName']
        if file.filename == '':
            return "No selected file", 404

        fileName = secure_filename(file.filename)
        file_extension = get_file_extension(fileName)
        if not allowed_conversions(file_extension, AUDIO_ALLOWED_EXTENSIONS):
            return f'The format "{file_extension}" is not allowed', 404

        newFormat = request.form["newFormat"].lower()
        if file_extension == newFormat:
            return "The file format and the new format can't be the same", 404

        if not allowed_conversions(newFormat, AUDIO_ALLOWED_EXTENSIONS):
            return f"The format {newFormat} is not allowed", 404

        time_stamp = datetime.utcnow()
        s3.put_object(Body=file,
                      Bucket=BUCKET_NAME,
                      Key=f"{user.username}/{UPLOAD_FOLDER}/{fileName}",
                      ContentType=request.mimetype)

        task = Task(fileName=fileName, newFormat=newFormat,
                    timeStamp=time_stamp, status='uploaded')
        user.tasks.append(task)
        session.commit()
        send_message(sqs_client, queue_url,{"username":user.username,"email":user.email,"task":task.id})
        return {"message": "Task successfully created.", "New Task": task_schema.dump(task)}

class ViewTask(Resource):

    @jwt_required()
    def get(self, id_task):
        user, task = get_user_task(get_jwt_identity(), id_task)
        if task:
            return task_schema.dump(task)
        return "Task not found in current user", 404

    @jwt_required()
    def put(self, id_task):
        user, task = get_user_task(get_jwt_identity(), id_task)
        if task:
            newFormat = request.json["newFormat"]
            if not allowed_conversions(newFormat, AUDIO_ALLOWED_EXTENSIONS):
                return f'The format"{newFormat}" is not allowed', 404
            
            if newFormat == task.newFormat:
                return f'This task is already configured with the given format ({newFormat})', 404

            if task.status == 'processed':
                remove_file(f"{user.username}/{DOWNLOAD_FOLDER}", f"{remove_extension(task.fileName)}.{task.newFormat}")

            task.status = 'uploaded'
            task.newFormat = request.json["newFormat"]
            task.timeStamp=datetime.utcnow()
            session.commit()
            send_message(sqs_client, queue_url,{"username":user.username,"email":user.email,"task":task.id})
            return task_schema.dump(task)

        return "Task not found in current user", 404

    @jwt_required()
    def delete(self, id_task):
        user, task = get_user_task(get_jwt_identity(), id_task)
        if task:
            remove_all_related_files(user.username, task.fileName, task.newFormat)
            session.delete(task)
            session.commit()
            return "Task removed", 200
        return "Task not found in current user", 404


class ViewFiles(Resource):

    @jwt_required()
    def get(self, filename):
        user = get_user(get_jwt_identity())
        if user:
            try:
                file_object = get_file(f"{user.username}/{UPLOAD_FOLDER}/{filename}")
            except Exception as e:
                try:
                    file_object = get_file(f"{user.username}/{DOWNLOAD_FOLDER}/{filename}")
                except:
                    return "File not found in current user.", 404

            return  Response(
                        file_object['Body'].read(),
                        mimetype='audio/mpeg',
                        headers={"Content-Disposition": f"attachment;filename={filename}.txt"}
                    )

        return "User no found.", 404


class ViewUser(Resource):

    @jwt_required()
    def delete(self):
        user = get_user(get_jwt_identity())
        if user:
            remove_user_dir(user.username)
            session.delete(user)
            session.commit()
            return "User delete", 200
        return "User not found", 404