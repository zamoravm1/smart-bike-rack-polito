import sys
import traceback
import os
from threading import Timer
import signal

import pymongo
# Path
path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f'{path}/../ultralytics/')
from ultralytics import YOLO

def EveryN(i, iter = 0):
    global bike_count
    global racks
    global pictures
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
    
    if connection:
        # Cursor of the pictures
        cursor_pictures = pictures.find({})
        
        pictures_list = list(cursor_pictures)
        
        if len(pictures_list) > 0:

            for document in pictures_list:
                filename = document['filename']
                filepath = f"{path}/pictures/{filename}"
                im_b64 = document['image_data']

                # Save the picture in a folder
                with open(filepath, 'wb') as f:
                    f.write(im_b64)
                
                
                rack_id = document['rack_id']
                
                cursor_rack = racks.find({})
                
                slots = 22
                
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
                    traceback.print_exc()
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

if __name__ == "__main__": 
    
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

    # Charge YOLO model
    train = 'train33.pt'
    model = YOLO(path + '/models/' + train)

    # Set thread
    timer = 300 # 5 minutes
    alive=True       
      
    try:
        EveryN(timer)
        signal.pause()
    except KeyboardInterrupt:
        alive=False