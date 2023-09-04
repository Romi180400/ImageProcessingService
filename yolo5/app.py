import os
import time
import uuid
from pathlib import Path

import boto3
import yaml
from detect import run
from flask import Flask, request, jsonify
from loguru import logger
from pymongo.mongo_client import MongoClient

images_bucket = os.environ['BUCKET_NAME']
s3 = boto3.client('s3')
mongo_client = MongoClient('mongodb://localhost:27107/')
db = mongo_client['prediction_db']
collection = db['predictions']


with open("data/coco128.yaml", "r") as stream:
    names = yaml.safe_load(stream)['names']


app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "health"}), 200


@app.route('/predict', methods=['POST'])
def predict():
    # Generates a UUID for this current prediction HTTP request. This id can be used as a reference in logs to identify and track individual prediction requests.
    prediction_id = str(uuid.uuid4())
    logger.info(f'prediction: {prediction_id}. start processing')
    # Receives a URL parameter representing the image to download from S3
    img_name = request.args.get('imgName')

    # TODO download img_name from S3, store the local image path in original_img_path
    #  The bucket name should be provided as an env var BUCKET_NAME.

    imageFinalName = img_name.split("/")[-1]
    local_dir = 'tmp/'
    os.makedirs(local_dir, exist_ok=True)
    original_img_path = local_dir + imageFinalName
    s3.download_file(images_bucket, img_name, original_img_path)

    logger.info(f'prediction: {prediction_id}/{original_img_path}. Download img completed')

    # Predicts the objects in the image
    run(
        weights='yolov5s.pt',
        data='data/coco128.yaml',
        source=original_img_path,
        project='static/data',
        name=prediction_id,
        save_txt=True
    )

    logger.info(f'prediction: {prediction_id}/{original_img_path}. done')

    # This is the path for the predicted image with labels
    # The predicted image typically includes bounding boxes drawn around the detected objects, along with class labels and possibly confidence scores.
    predicted_img_path = Path(f'static/data/{prediction_id}/{imageFinalName}')

    # TODO Uploads the predicted image (predicted_img_path) to S3 (be careful not to override the original image).

    new_img_name = f"predicted_{imageFinalName}"
    # predicted_img_path = f'predicted_{new_img_name}'
    os.rename(f'/usr/src/app/static/data/{prediction_id}/{imageFinalName}', f'/usr/src/app/static/data/{prediction_id}/{new_img_name}')
    predicted_for_upload = '/'.join(img_name.split('/')[:-1]) + f'/{new_img_name}'
    new_local_to_uplaod = f'/usr/src/app/static/data/{prediction_id}/{new_img_name}'
    s3.upload_file(new_local_to_uplaod, images_bucket, predicted_for_upload)
    os.rename(f'/usr/src/app/static/data/{prediction_id}/{new_img_name}',f'/usr/src/app/static/data/{prediction_id}/{imageFinalName}')

    # Parse prediction labels and create a summary
    pred_summary_path = Path(f'static/data/{prediction_id}/labels/{original_img_path.split(".")[0]}.txt')
    if pred_summary_path.exists():
        with open(pred_summary_path) as f:
            labels = f.read().splitlines()
            labels = [line.split(' ') for line in labels]
            labels = [{
                'class': names[int(l[0])],
                'cx': float(l[1]),
                'cy': float(l[2]),
                'width': float(l[3]),
                'height': float(l[4]),
            } for l in labels]

        logger.info(f'prediction: {prediction_id}/{original_img_path}. prediction summary:\n\n{labels}')

        prediction_summary = {
            'prediction_id': prediction_id,
            'original_img_path': original_img_path,
            'predicted_img_path': predicted_img_path,
            'labels': labels,
            'time': time.time()
        }

        # TODO store the prediction_summary in MongoDB
        collection.insert_one(prediction_summary)

        return prediction_summary.json()
    else:
        return f'prediction: {prediction_id}/{original_img_path}. prediction result not found', 404


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081)
