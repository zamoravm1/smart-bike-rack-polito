import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import json
import time
import math
import pymongo
from pymongo import MongoClient
import datetime
import pytz

class SmartRackChatbot:
    def __init__(self, token):
        self.token = token
        self.bot = telebot.TeleBot(token)
        
        self.locations = []
        self.language_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        self.language_keyboard.row(KeyboardButton('Italiano'), KeyboardButton('English'))
        self.client = MongoClient("mongodb+srv://smartrack2022:Smart*rack2022@smartbikerack.ocijvrf.mongodb.net/test")
        self.db = self.client["Smart_Bike_Rack"]
        self.rack_id = 1
        
        self.rack_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        self.rack_keyboard.row(KeyboardButton('R1'), KeyboardButton('R2'), KeyboardButton('R2'), KeyboardButton('R3'))
        self.rack_keyboard.row(KeyboardButton("Back to start"), KeyboardButton("Help"))


    def read_BikeCount(self):
        # Select the database and collection
        bike_count = self.db["Bike_Count"]   
        # Find the last document in the collection with the specified rack_id
        document = bike_count.find({'rack_id': self.rack_id}).sort([('timestamp', pymongo.DESCENDING)]).limit(1)[0]
        free_slot = document['free_slots']
        timestamp = document['timestamp']
        print("Free Slots: ", document['free_slots'])
        print("Timestamp: ", document['timestamp'])
        return free_slot
        
    def read_Forecast(self):
        # Select the database and collection
        bike_forecasting = self.db["Forecasting"]

        # Find the last document in the collection with the specified rack_id
        documents = bike_forecasting.find({'rack_id': self.rack_id}).sort([('timestamp', pymongo.DESCENDING)]).limit(4)
        
        # Initialize empty lists for free_slots and timestamps
        free_slots = []
        timestamps = []

        # Loop through the documents and retrieve the free_slots and timestamp fields
        for document in documents:
            free_slots.append(document['free_slots'])
            timestamps.append(document['timestamp'])

        # Return the lists as a tuple
        return free_slots
    
    def get_message_text(self):
        timezone = pytz.timezone('Europe/Rome')
        now = datetime.datetime.now(timezone)
        message_text = "NOW - Free slots (" + now.strftime('%H:%M') + "): " + str(self.read_BikeCount()) + "\n"
        forecasting =  self.read_Forecast()
        one_hour_later = now + datetime.timedelta(hours=1)
        two_hour_later = now + datetime.timedelta(hours=2)
        if now.minute < 30:
            message_text += "Free slots (" + now.strftime('%H') + ":30): "+ str(forecasting[0]) + "\n"
            message_text += "Free slots (" + one_hour_later.strftime('%H') + ":00): "+ str(forecasting[1]) +  "\n"
            message_text += "Free slots (" + one_hour_later.strftime('%H') + ":30): "+ str(forecasting[2]) +  "\n"
        else:
            message_text += "Free slots (" + one_hour_later.strftime('%H') + ":00): "+ str(forecasting[0]) +"\n"
            message_text += "Free slots (" + one_hour_later.strftime('%H') + ":30): "+ str(forecasting[1]) +"\n"
            message_text += "Free slots (" + two_hour_later.strftime('%H') + ":30): "+ str(forecasting[2]) +"\n"
        return message_text


    def start(self):
        # Load the locations from the json file
        with open('zones.json', 'r') as f:
            self.locations = json.load(f)

        @self.bot.message_handler(commands=['start'])
        def start(message):
            # Send a message asking for language selection
            self.bot.reply_to(message, "Pick your preferred language:", reply_markup=self.language_keyboard)

        # Handle language selection
        @self.bot.message_handler(func=lambda message: message.text in ["Italiano", "English"])
        def process_language_selection(message):
            if message.text == "Italiano":
                self.bot.reply_to(message, "Supporto per l'italiano non ancora disponibile.")
            if message.text == "English":
                # Ask the user to select a zone
                zone_buttons = ReplyKeyboardMarkup(resize_keyboard=True)
                buttons = []
                lines = math.ceil(len(self.locations['features']) / 4)
                for i in range(1, lines+1):
                    for j in range(1, 5):
                        # Number of remaining features
                        if j <= len(self.locations['features']) - 4 * (i - 1):
                            # Last feature in the row.
                            #button_text = self.locations['features'][j + 3 * (i - 1)]['properties']['name']
                            button_text = str((i - 1)*4 + j)
                            button = KeyboardButton(button_text)
                            buttons.append(button)
                    zone_buttons.row(*buttons)
                    buttons = []
            zone_buttons.row(KeyboardButton("Back to start"), KeyboardButton("Help"))
            
            # Send the picture of the zones
            with open('zones.png', 'rb') as photo:
                self.bot.send_photo(message.chat.id, photo)
            # Pause for a few seconds to allow the photo to be sent before sending the message and the number buttons
            time.sleep(1)
            self.bot.reply_to(message, "From the picture above, select the area you are going to:", reply_markup=zone_buttons)
        # Handle zone selection
        @self.bot.message_handler(func=lambda message: message.text in ["5"])
        def process_zone_selection(message):
            # Get the selected zone
            #selected_zone = next((zone for zone in self.locations['features'] if zone['properties']['name'] == message.text), None)
            if message.text == "5":
                # Send the picture of the racks in the zone
                with open('racks.png', 'rb') as photo:
                    self.bot.send_photo(message.chat.id, photo)
                
                # Pause for a few seconds to allow the photo to be sent before sending the message and the number buttons
                time.sleep(1)

                message_text = "*State of racks in the zone:*\n\n"  # Add two newlines to create a gap between the title and the list
                message_text += self.get_message_text()
                
                # Send the message using the reply_to method of the bot object
                self.bot.reply_to(message, message_text, reply_markup= self.rack_keyboard)
                
                if message.text is not None:
                    self.bot.reply_to(message, "code under construction from this point.") 
                    
                else:
                    self.bot.reply_to(message, "Invalid rack selection or not available.")   
            else:
                self.bot.reply_to(message, "Invalid zone selection or not available.")
                print(message.text)
            
        '''        
        # Handle rack selection
        @self.bot.message_handler(func=lambda message: message.text in ["R1"])
        '''   
        # Start the bot
        self.bot.infinity_polling()
        
if __name__ == '__main__':
    bot = SmartRackChatbot("5856399288:AAEUv-kY9oJ1PxLGThO0wviLfp30LNUdblI")
    bot.start()
