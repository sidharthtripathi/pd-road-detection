import pika
import pymongo
import os
import json
from main import RoadDefectDetector
from appwrite_local.appwrite import storage
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["roadvision"]
videos_collection = db["videos"]
images_collection = db["images"]

def callback(ch, method, properties, body):
    detector = RoadDefectDetector('yolo-pd.pt')
    message_data = json.loads(body.decode('utf-8'))
    type = message_data["type"]
    id = message_data["id"]
    file_name = storage.get_file(file_id=id, bucket_id="6894b90a002c1e18828b")["name"]
    open(file_name, "wb").write(storage.get_file_download(file_id=id,bucket_id="6894b90a002c1e18828b"))
    if type == "img":
        result = detector.process_image(file_name)
        images_collection.insert_one(result)
    elif type == "vid":
        result = detector.process_video(file_name)
        videos_collection.insert_one(result)
    
    os.remove(file_name)
    

        


try:
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.basic_consume(queue='roadvision', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()
except KeyboardInterrupt:
    print("Shutting down gracefully...")
    try:
        channel.stop_consuming()
        connection.close()
    except Exception:
        pass