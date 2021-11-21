import yaml

config_path = './config.yml'

with open(r'' + config_path) as file:
    config = yaml.full_load(file)
    UPLOAD_FOLDER = config["app-config"]["UPLOAD_FOLDER"]
    DOWNLOAD_FOLDER = config["app-config"]["DOWNLOAD_FOLDER"]
    AWS_ACCESS_KEY_ID = config["aws"]["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = config["aws"]["AWS_SECRET_ACCESS_KEY"]
    AWS_SESSION_TOKEN = config["aws"]["AWS_SESSION_TOKEN"]
    BUCKET_NAME = config["aws"]["BUCKET_NAME"]

