#!/bin/bash
apt update -y
docker image rm -f $(docker image ls -q)
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
mkdir -p /home/app
cd /home/app
git clone https://github.com/anderson0365/miso-softwarecloud-gr-17.git
cd /home/app/miso-softwarecloud-gr-17/instancia-worker
/usr/local/bin/docker-compose up -d