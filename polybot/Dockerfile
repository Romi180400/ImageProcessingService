FROM python:3.10-alpine
LABEL authors="romibox-deb"
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python3", "app.py"]