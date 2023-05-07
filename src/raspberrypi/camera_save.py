import signal
from threading import Timer
import cv2
import datetime
import pymongo
import os

# Connect to MongoDB database
try:
    myclient = pymongo.MongoClient("mongodb+srv://smartrack2022:*************************")
    mydb = myclient["Smart_Bike_Rack"]
    mycol = mydb["Pictures"]
    connection = True
except:
    connection = False

# Set up video capture object to capture video from default camera
cap = cv2.VideoCapture(0)

# Open camera for 60 seconds to allow it to autofocus
for i in range(60):
    ret, frame = cap.read()
    if not ret:
        continue
    cv2.waitKey(1)
    
# Initialize index and time variables
index = 1
timer = 300
alive=True

# Path 
path = os.path.dirname(os.path.abspath(__file__))

def EveryN(i, iter):
    global connection
    if not alive:
        return
    Timer(i, EveryN, (i, iter+1)).start()
    
    now = datetime.datetime.now()
    if (now.hour >= 7 and now.hour <= 19) and (now.weekday() != 5 and now.weekday() != 6):
        if not connection:
            try:
                myclient = pymongo.MongoClient("mongodb+srv://smartrack2022:*************************")
                mydb = myclient["Smart_Bike_Rack"]
                mycol = mydb["Pictures"]
                connection = True
            except:
                connection = False
        
        # Capture a frame from the video feed
        ret, frame = cap.read()

        # Save the frame to file system
        filename = f"test{iter}-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.jpg"
        filepath = f"{path}/pictures/{filename}"
        cv2.imwrite(filepath, frame)

        # Insert metadata into MongoDB database
        with open(filepath, 'rb') as f:
            data = f.read()
        doc = {
        "rack_id" : 1,    
        'filename': filename,
        'timestamp': datetime.datetime.now(),
        'image_data': data,
        }
        try:
            mycol.insert_one(doc)
        except:
            connection = False
            with open(path + 'error.txt', 'a') as f:
                f.write(str(filename) + " was not added to mongodb\n")
                
try:
    EveryN(timer,index)
    signal.pause()
except KeyboardInterrupt:
    alive=False


