import os

import flask
from flask import request

from bot import ObjectDetectionBot

app = flask.Flask(__name__)

# TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
# TELEGRAM_APP_URL = os.environ['TELEGRAM_APP_URL']
TELEGRAM_TOKEN_FILE = os.environ['TELEGRAM_TOKEN_FILE']
with open(TELEGRAM_TOKEN_FILE, 'r') as file:
    TELEGRAM_TOKEN = file.read().rstrip()

TELEGRAM_APP_URL_FILE = os.environ['TELEGRAM_APP_URL_FILE']
with open(TELEGRAM_APP_URL_FILE, 'r') as file:
    TELEGRAM_APP_URL = file.read().rstrip()

BUCKET_NAME_FILE = os.environ['BUCKET_NAME_FILE']
with open(BUCKET_NAME_FILE, 'r') as file:
    BUCKET_NAME = file.read().rstrip()

YOLO5_CONT_NAME = os.environ['YOLO5_CONT_NAME']

@app.route('/', methods=['GET'])
def index():
    return 'Ok'


@app.route(f'/{TELEGRAM_TOKEN}/', methods=['POST'])
def webhook():
    req = request.get_json()
    print(req)
    bot.handle_message(req['message'])
    return 'Ok'


if __name__ == "__main__":

    bot = ObjectDetectionBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL)
app.run(host='0.0.0.0', port=8443)