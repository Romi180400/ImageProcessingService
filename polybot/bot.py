import os
import time

import boto3
import requests
import telebot
from botocore.exceptions import ClientError
from loguru import logger
from telebot.types import InputFile

from polybot.img_proc import Img


class Bot:

    def __init__(self, token, telegram_chat_url, bucket_name, yolo5_cont_name):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/', timeout=60)

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

        self.bucket_name = bucket_name
        self.yolo5_cont_name = yolo5_cont_name

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        if 'text' in msg:
            self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])


class ImageProcessingBot(Bot):
    def __init__(self, token, telegram_chat_url):
        super().__init__(token, telegram_chat_url)
        self.processing_completed = True

    def handle_message(self, msg):
        if not self.processing_completed:
            logger.info("Previous message processing is not completed. Ignoring current message.")
            return

        if "photo" in msg:
            # If the message contains a photo, check if it also has a caption
            if "caption" in msg:
                caption = msg["caption"]
                if "concat" in caption.lower():
                    self.process_image(msg)
                if "contour" in caption.lower():
                    self.process_image_contur(msg)
                if "rotate" in caption.lower():
                    self.process_image_rotate(msg)
                if "segment" in caption.lower():
                    self.process_image_segment(msg)
                if "salt and pepper" in caption.lower():
                    self.process_image_salt_n_pepper(msg)
            else:
                self.send_text(msg['chat']['id'],
                               f'Please one of the following captions to alternate the picture: concat, conture, salt and pepper, segment, rotate.')
        elif "text" in msg:
            super().handle_message(msg)

    def process_image(self, msg):
        self.processing_completed = False

        # Download the two photos sent by the user
        image_path = self.download_user_photo(msg)
        another_image_path = self.download_user_photo(msg)

        # Create two different Img objects from the downloaded images
        image = Img(image_path)
        another_image = Img(another_image_path)

        # Process the image using your custom methods (e.g., apply filter)
        image.concat(another_image)  # Concatenate the two images

        # Save the processed image to the specified folder
        processed_image_path = image.save_img()

        if processed_image_path is not None:
            # Send the processed image back to the user
            self.send_photo(msg['chat']['id'], processed_image_path)

        self.processing_completed = True

    def process_image_contur(self, msg):
        self.processing_completed = False

        # Download the two photos sent by the user
        image_path = self.download_user_photo(msg)

        # Create two different Img objects from the downloaded images
        image = Img(image_path)

        # Process the image using your custom methods (e.g., apply filter)
        image.contour()  # contur the image

        # Save the processed image to the specified folder
        processed_image_path = image.save_img()

        if processed_image_path is not None:
            # Send the processed image back to the user
            self.send_photo(msg['chat']['id'], processed_image_path)

        self.processing_completed = True

    def process_image_rotate(self, msg):
        self.processing_completed = False

        # Download the two photos sent by the user
        image_path = self.download_user_photo(msg)

        # Create two different Img objects from the downloaded images
        image = Img(image_path)

        # Process the image using your custom methods (e.g., apply filter)
        image.rotate()  # rotate the image

        # Save the processed image to the specified folder
        processed_image_path = image.save_img()

        if processed_image_path is not None:
            # Send the processed image back to the user
            self.send_photo(msg['chat']['id'], processed_image_path)

        self.processing_completed = True

    def process_image_salt_n_pepper(self, msg):
        self.processing_completed = False

        image_path = self.download_user_photo(msg)

        image = Img(image_path)

        image.salt_n_pepper()

        processed_image_path = image.save_img()

        if processed_image_path is not None:
            self.send_photo(msg['chat']['id'], processed_image_path)

            self.processing_completed = True

    def process_image_segment(self, msg):
        self.processing_completed = False

        image_path = self.download_user_photo(msg)

        image = Img(image_path)

        image.segment()

        processed_image_path = image.save_img()

        if processed_image_path is not None:
            self.send_photo(msg['chat']['id'], processed_image_path)

        self.processing_completed = True


class ObjectDetectionBot(Bot):

    def __init__(self, token, telegram_chat_url, bucket_name, yolo5_cont_name):
        super().__init__(token, telegram_chat_url, bucket_name, yolo5_cont_name)
        self.processing_completed = True
        self.s3_client = boto3.client('s3')

    def request_yolo5_prediction(self, img_name):
        yolo5_cont_name = self.yolo5_cont_name
        yolo5_api_url = f'http://{yolo5_cont_name}:8081/predict'
        try:
            response = requests.post(f"{yolo5_api_url}?imgName={img_name}")
            return response
        except requests.exceptions.HTTPError as e:
            logger.info(f'yolo requests Error: {e}')
            response.raise_for_status()
            return None

    def count_object_prediction(self, json_summary):
        summary_labels = json_summary['labels']
        counted_objects = {}
        for item in summary_labels:
            counted_objects[item['class']] = counted_objects.get(item['class'], 0) + 1
        formatted_message = ''
        for key, value in counted_objects.items():
            formatted_key = key.capitalize()
            formatted_message += f'{formatted_key}: {value}\n'
        return formatted_message

    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if self.is_current_msg_photo(msg):
            photo_path = self.download_user_photo(msg)
            bucket_name = self.bucket_name
            object_name = f'telegram_photos/{photo_path}'
        try:
            self.s3_client.upload_file(photo_path, bucket_name, object_name)
            logger.info(f'Successfully uploaded {photo_path} to {bucket_name}/{object_name}')

            prediction_result = self.request_yolo5_prediction(object_name)
            if prediction_result is None:
                url_objects = print("https://github.com/ultralytics/yolov5/discussions/7370")
                self.send_text(msg['chat']['id'],
                               f'No predicitons found, please try upload another image contains some of the following list objects: {url_objects}')
            else:
                prediction_data = prediction_result.json()
                counted_prediction_result = self.count_object_prediction(prediction_data)
                self.send_text(msg['chat']['id'], f'Predicted Objects: \n{counted_prediction_result}')

        except ClientError as e:
            logger.error(f'An error occurred: {e}')
            self.send_text(msg['chat']['id'], 'An error occurred while processing your request.')
        except Exception as e:
            logger.error(f'Unexceptional: error: {e}')
            self.send_text(msg['chat']['id'], 'An unexpected error occurred, Please try again.')