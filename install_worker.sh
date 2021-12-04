#!bin/bash
apt update
docker image rm -f $(docker image ls -q)
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt -y remove python3.6
apt -y install python3.8 build-essential ffmpeg postgresql-server-dev-all libpython3.8-dev python3-pip
rm -rf /usr/bin/python
ln -s /usr/bin/python3 /usr/bin/python
mkdir /home/app
cd /home/app
git clone https://github.com/anderson0365/miso-softwarecloud-gr-17.git
cd miso-softwarecloud-gr-17/despliegue-6/flaskr
pip install --no-cache-dir -r requirements.txt
pip install --no-cache-dir boto3
cp config.yml ../worker/
cd ../worker
python tasks.py
