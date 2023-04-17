import os
from threading import Timer
import signal

import pymongo
from ultralytics import YOLO

# Connection to mongodb from pymongo
try:
    myclient = pymongo.MongoClient("mongodb+srv://smartrack2022:Smart*rack2022@smartbikerack.ocijvrf.mongodb.net/test")
    mydb = myclient["Smart_Bike_Rack"]
    bike_count = mydb["Bike_Count"]
    pictures = mydb["Pictures"]
    racks = mydb["Racks"]
    connection = True
except:
    connection = False

# Path
path = os.path.dirname(os.path.abspath(__file__))

# Charge YOLO model
train = 'train33'
model = YOLO(path + '/models/' + train)


timer = 300 # 5 minutes
alive=True

def EveryN(i, iter = 0):
    global connection
    if not alive:
        return
    Timer(i, EveryN, (i, iter+1)).start()
    
    if not connection:
        try:
            myclient = pymongo.MongoClient("mongodb+srv://smartrack2022:Smart*rack2022@smartbikerack.ocijvrf.mongodb.net/test")
            mydb = myclient["Smart_Bike_Rack"]
            bike_count = mydb["Bike_Count"]
            pictures = mydb["Pictures"]
            racks = mydb["Racks"]
            connection = True
        except:
            connection = False
            
    # Cursor of the pictures
    cursor_pictures = pictures.find({})

    for document in cursor_pictures:
        filename = document['filename']
        filepath = f"{path}/pictures/{filename}"
        im_b64 = document['image_data']

        # Save the picture in a folder
        with open(filepath, 'wb') as f:
            f.write(im_b64)
        
        
        rack_id = 1 # Change 1 with document['rack_id']
        
        cursor_rack = racks.find({})
        
        # Search the rack by id and look for the slots of the rack
        for rack in cursor_rack:
            if rack['rack_id'] == rack_id:
                slots = rack['slots']
                break
        
        # Predict the number of bikes using the model
        bikes = len(model(filepath)[0].boxes)
        
        # Define the document to insert
        count_example = {"rack_id" : rack_id,
        "timestamp" : filename[-23::][0:19],
        "free_slots" : slots - bikes,
        "busy_slots" : bikes,
        }
        
        # Insert the document in the collection bike_count
        try:
            bike_count.insert_one(count_example)
        except:
            connection = False
            with open(path + 'error.txt', 'a') as f:
                f.write(str(filename) + " was not added to mongodb\n")
        
        # Delete the document from the collection pictures
        try: 
            pictures.delete_many({"filename" : document['filename']})
        except:
            connection = False
            with open(path + 'error.txt', 'a') as f:
                f.write(str(filename) + " was not deleted in mongodb\n")
           
try:
    EveryN(timer)
    signal.pause()
except KeyboardInterrupt:
    alive=False