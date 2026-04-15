#!/bin/bash

while ! nc -z db 5432; do
  sleep 2
  echo "Waiting postgress...."
done


python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput

python3 manage.py runserver 0.0.0.0:${WEB_PORT:-8000}

exit $?