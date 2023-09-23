#!/bin/bash

if [ "$REPO_NAME" == "web" ]; then
    gunicorn test_app:server -b 0.0.0.0:60000
elif [ "$REPO_NAME" == "worker" ]; then
    celery -A celery_app.celery worker --loglevel=info --pool threads
elif [ "$REPO_NAME" == "beat" ]; then
    celery -A celery_app.celery beat --loglevel=info
else
    echo "Invalid value for REPO_NAME: $REPO_NAME"; exit 1
fi
