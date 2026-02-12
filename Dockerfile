FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
ENTRYPOINT ["sh", "-c"]
EXPOSE 8000
CMD ["python manage.py migrate --fake-initial --noinput && python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8000 webproj.wsgi:application"]