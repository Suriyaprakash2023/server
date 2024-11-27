#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Run migrations to set up the database
python manage.py makemigrations
python manage.py migrate

# Collect static files (optional, remove if not using static files)
# python manage.py collectstatic --noinput

# You do not need to start the Django server with `runserver` on Vercel.
