#!bin/bash
apt update
docker image rm -f $(docker image ls -q)
mkdir /home/app
cd /home/app
git clone https://github.com/anderson0365/miso-softwarecloud-gr-17.git
cd miso-softwarecloud-gr-17/despliegue-6/flaskr
apt -y install build-base ffmpeg postgresql-dev bash python3 python3-dev py3-pip
ln -s /usr/bin/python3 /usr/bin/python
pip install --no-cache-dir -r requirements.txt --ignore-installed six
pip install --no-cache-dir pydub gunicorn boto3
mv wsgi.py ../
cp config.yml ../
chmod 777 start-celery.sh start-flask.sh wait-for-it.sh
./start-celery.sh