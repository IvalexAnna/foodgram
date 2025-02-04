FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

RUN python manage.py makemigrations && python manage.py migrate

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram_backend.foodgram_backend.wsgi"]