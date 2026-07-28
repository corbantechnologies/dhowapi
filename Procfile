web: python manage.py migrate && gunicorn dhowapi.wsgi:application --bind 0.0.0.0:$PORT --timeout 300 --graceful-timeout 120
