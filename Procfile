web: python manage.py migrate && playwright install chromium && playwright install-deps && gunicorn dhowapi.wsgi:application --bind 0.0.0.0:$PORT --timeout 300 --graceful-timeout 120
