web: daphne simplee_rpa.asgi:application --port $PORT --bind 0.0.0.0 -v2
celeryworker: celery -A simplee_rpa worker 
release: python manage.py migrate
beat: celery -A simplee_rpa beat