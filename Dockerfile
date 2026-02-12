FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app/
RUN mkdir -p /app/static /app/staticfiles /app/media
ENTRYPOINT ["sh", "-c"]
EXPOSE 8000
CMD ["python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8000 webproj.wsgi:application"]