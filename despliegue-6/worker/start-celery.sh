#!/usr/bin/env bash

cd /home/app
celery -A  flaskr.tasks.tasks worker -B -l info
