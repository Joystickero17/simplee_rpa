web: gunicorn simplee_rpa.wsgi
celeryworker: celery -A simplee_rpa worker 
release: python manage.py migrate
beat: celery -A simplee_rpa beat