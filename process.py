from dotenv import load_dotenv
load_dotenv()
import pika
import pymongo
import os
import json
from main import RoadDefectDetector
from appwrite_local.appwrite import storage

mongo_client = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = mongo_client[os.getenv("MONGO_COLLECTION")]
videos_collection = db["videos"]
images_collection = db["images"]

def callback(ch, method, properties, body):
    detector = RoadDefectDetector('yolo-pd.pt')
    message_data = json.loads(body.decode('utf-8'))
    id = message_data["id"]
    bucket_id = message_data["bucketID"]
    file_metadata = storage.get_file(file_id=id, bucket_id=bucket_id)
    type = "img" if file_metadata["mimeType"].startswith("image/") else "vid"
    file_name = file_metadata["name"]
    open(file_name, "wb").write(storage.get_file_download(file_id=id,bucket_id=bucket_id))
    if type == "img":
        result = detector.process_image(file_name)
        result["trackingID"] = id
        images_collection.insert_one(result)
    elif type == "vid":
        result = detector.process_video(file_name)
        result["trackingID"] = id
        videos_collection.insert_one(result)
    
    os.remove(file_name)
    

        


try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(os.getenv("RABBIT_URI")))
    channel = connection.channel()
    channel.basic_consume(queue="roadvision", on_message_callback=callback, auto_ack=True)
    channel.start_consuming()
except KeyboardInterrupt:
    print("Shutting down gracefully...")
    try:
        channel.stop_consuming()
        connection.close()
    except Exception:
        pass