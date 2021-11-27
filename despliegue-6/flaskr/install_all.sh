#!bin/bash
# ejecutar dentro de carpeta de flask
sudo apt update
sudo docker image rm -f $(docker image ls -q)
sudo apt upgrade
sudo apt -y install build-base ffmpeg postgresql-dev bash python3 python3-dev py3-pip
sudo ln -s /usr/bin/python3 /usr/bin/python
pip install --no-cache-dir -r requirements.txt --ignore-installed six
pip install --no-cache-dir pydub gunicorn boto3
WORKDIR /home/app/flaskr
sudo mv wsgi.py ../
sudo cp config.yml ../
sudo chmod 777 start-celery.sh start-flask.sh wait-for-it.sh