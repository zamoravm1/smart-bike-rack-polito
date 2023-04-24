# Last update 24.04.23 21:22 happy english path full with emojis

# By: @zamoravm1 10.04.2023
#! pip install telebot
#! pip install pymongo

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton,ReplyKeyboardRemove,InlineKeyboardMarkup, InlineKeyboardButton



import json
import time
import math
import pymongo
from pymongo import MongoClient
import datetime
import pytz
import re

class SmartRackChatbot:
    def __init__(self, token):
        self.token = token
        self.bot = telebot.TeleBot(token)
        
        self.locations = []
        self.language_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        self.language_keyboard.row(KeyboardButton('Italiano'), KeyboardButton('English'))
        self.client = MongoClient("mongodb+srv://smartrack2022:Smart*rack2022@smartbikerack.ocijvrf.mongodb.net/test")
        self.db = self.client["Smart_Bike_Rack"]
        
        
        self.rack_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        self.rack_keyboard.row(KeyboardButton('Rack #1'), KeyboardButton('Rack #2'), KeyboardButton('Rack #3'))
        self.rack_keyboard.row(KeyboardButton("Select another zone"), KeyboardButton("Help"))
        
        self.rack2_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        self.rack2_keyboard.row(KeyboardButton('Rack #1'), KeyboardButton('Rack #2'), KeyboardButton('Rack #3'))
        self.rack2_keyboard.row(KeyboardButton('Update racks state'),KeyboardButton('Select another zone'),KeyboardButton("Help"))
        
        self.racks=[1,1,1]
        self.rack=1
        
        self.labels=[]


    def read_BikeCount(self):
        # Select the database and collection
        bike_count = self.db["Bike_Count"]   
        # Find the last document in the collection with the specified rack_id
        document = bike_count.find({'rack_id': self.rack}).sort([('timestamp', pymongo.DESCENDING)]).limit(1)[0]
        free_slot = document['free_slots']
        timestamp = document['timestamp']
        print("Free Slots: ", document['free_slots'])
        print("Timestamp: ", document['timestamp'])
        return free_slot
        
    def read_Forecast(self):
        # Select the database and collection
        bike_forecasting = self.db["Forecasting"]

        # Find the last document in the collection with the specified rack_id
        documents = bike_forecasting.find({'rack_id': self.rack}).sort([('timestamp', pymongo.DESCENDING)]).limit(4)
        
        # Initialize empty lists for free_slots and timestamps
        free_slots = []
        timestamps = []

        # Loop through the documents and retrieve the free_slots and timestamp fields
        for document in documents:
            free_slots.append(document['free_slots'])
            timestamps.append(document['timestamp'])

        # Return the lists as a tuple
        return free_slots
    def read_Localization(self,rack):
        # Select the database and collection
        loc = self.db["Racks"]   
        # Find the last document in the collection with the specified rack_id
        document = loc.find({'rack_id': rack})
        latitude = document['localization']['latitude']
        longitude = document['localization']['longitude']
        return longitude, latitude
    
#     # Original get_message_text that can work in the case of several racks working by zone
#     def get_message_text(self):
#         timezone = pytz.timezone('Europe/Rome')
#         now = datetime.datetime.now(timezone)
#         message_text="\n"
#         c=0
#         for i in self.racks:
#             c+=1
#             self.rack=i
#             print(i)
#             message_text += "\U0001F6B2 *Rack *"+ str(c) + ":\n"
#             message_text += "Real-time free slots (" + now.strftime('%H:%M') + "): " + str(self.read_BikeCount()) + "\n"

#             forecasting =  self.read_Forecast()
#             one_hour_later = now + datetime.timedelta(hours=1)
#             two_hour_later = now + datetime.timedelta(hours=2)
#             if now.minute < 30:
#                 message_text += "Estimated free spaces at " + now.strftime('%H') + ":30 : "+ str(forecasting[0]) + "\n"
#                 message_text += "Estimated free spaces at " + one_hour_later.strftime('%H') + ":00: "+ str(forecasting[1]) +  "\n"
#                 message_text += "Estimated free spaces at " + one_hour_later.strftime('%H') + ":30): "+ str(forecasting[2]) +  "\n"
#             else:
#                 message_text += "Estimated free spaces at " + one_hour_later.strftime('%H') + ":00): "+ str(forecasting[0]) +"\n"
#                 message_text += "Estimated free spaces at " + one_hour_later.strftime('%H') + ":30): "+ str(forecasting[1]) +"\n"
#                 message_text += "Estimated free spaces at " + two_hour_later.strftime('%H') + ":30): "+ str(forecasting[2]) +"\n"
#                 message_text += "\n"
#         return message_text

    #get message with racks state
    def get_message_text(self):
        timezone = pytz.timezone('Europe/Rome')
        now = datetime.datetime.now(timezone)
        message_text="\n"
        self.rack = 1
        print("get_message_text working")
        message_text += "\U00002705 *Rack #2:*\n"
        message_text += "Real-time free slots (" + now.strftime('%H:%M') + "): " + str(self.read_BikeCount()) + "\n"

        forecasting =  self.read_Forecast()
        one_hour_later = now + datetime.timedelta(hours=1)
        two_hour_later = now + datetime.timedelta(hours=2)
        if now.minute < 30:
            message_text += "Estimated free spaces at " + now.strftime('%H') + ":30 : "+ str(forecasting[0]) + "\n"
            message_text += "Estimated free spaces at " + one_hour_later.strftime('%H') + ":00: "+ str(forecasting[1]) +  "\n"
            message_text += "Estimated free spaces at " + one_hour_later.strftime('%H') + ":30): "+ str(forecasting[2]) +  "\n"
            
        else:
            message_text += "Estimated free spaces at " + one_hour_later.strftime('%H') + ":00): "+ str(forecasting[0]) +"\n"
            message_text += "Estimated free spaces at " + one_hour_later.strftime('%H') + ":30): "+ str(forecasting[1]) +"\n"
            message_text += "Estimated free spaces at " + two_hour_later.strftime('%H') + ":30): "+ str(forecasting[2]) +"\n"
        message_text += "\n*Rock tip!*\n\U0001F91F If less than 3 free slots, it's better to go for another rack.\n"
            
        return message_text
    
    def zone_selection(self):
        # Ask the user to select a zone
        zone_buttons = ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = []
        self.labels = []
        lines = math.ceil(len(self.locations['features']) / 4)
        for i in range(1, lines+1):
            for j in range(1, 5):
                # Number of remaining features
                if j <= len(self.locations['features']) - 4 * (i - 1):
                    # Last feature in the row.
                    button_text = self.locations['features'][j + 4 * (i - 2)]['properties']['name']
                    #button_text = str((i - 1)*4 + j)
                    button = KeyboardButton(button_text)
                    buttons.append(button)
                    self.labels.append(button_text)
            zone_buttons.row(*buttons)
            buttons = []
        zone_buttons.row(KeyboardButton("Help"))
        return zone_buttons

    def start(self):
        # Load the locations from the json file
        with open('zones_byname.json', 'r') as f:
            self.locations = json.load(f)

        @self.bot.message_handler(commands=['start'])
        def start(message):
            # Send a message asking for language selection
            self.bot.reply_to(message, "*Here we go! \U0001F60E\nPick your preferred language:*", reply_markup=self.language_keyboard,parse_mode='Markdown')

        # Handle language selection
        @self.bot.message_handler(func=lambda message: message.text in ["Italiano", "English"]  or message.text == "Select another zone" )
        def process_language_selection(message):
            if message.text == "Italiano":
                self.bot.reply_to(message, "Supporto per l'italiano non ancora disponibile.")
            if message.text == "English"  or message.text == "Select another zone":
                zone_buttons=self.zone_selection()
            else:
                self.bot.reply_to(message, "Invalid zone selection or not available.")
                print(message.text)
            
            # Send the picture of the zones
            with open('zones_byname.jpg', 'rb') as photo:
                self.bot.send_photo(message.chat.id, photo)
            #self.bot.reply_to(message, "Zones with racks are marked by *green tags* in the picture above. \nFor now,  available only the 'Aula M-N' zone.\n*Select or write the zone you need to go:*", reply_markup=zone_buttons)
            self.bot.reply_to(message,'\U0001F7E2 *Select or write the zone (green marks in the picture above):*\n', reply_markup=zone_buttons,parse_mode='Markdown')
            self.bot.reply_to(message,'_For now, available only "Aula M-N"_', reply_markup=zone_buttons,parse_mode='Markdown')
        # Handle zone selection
        @self.bot.message_handler(func=lambda message: message.text in self.labels or message.text== "Update racks state")
        def process_zone_selection(message):
            # Get the selected zone
            #selected_zone = next((zone for zone in self.locations['features'] if zone['properties']['name'] == message.text), None)
            if message.text == "Aula M-N" or message.text== "Update racks state":
                print(" process_zone_selection running: " + message.text)
                # Send the picture of the racks in the zone
                with open('racks.png', 'rb') as photo:
                    self.bot.send_photo(message.chat.id, photo)
                
                message_text = "*Select or write a rack to get the map localization:*\n"  # Add two newlines to create a gap between the title and the list
                
                racks = [1,1,1]
                self.racks = racks
                message_text += self.get_message_text()
                #button = InlineKeyboardButton("Update this info", callback_data="button_callback")
                # Create the markup with the button
                #markup = InlineKeyboardMarkup().add(button)
                
                # Send the message with the markup
                #self.bot.send_message(message.chat.id, message_text, reply_markup=markup,parse_mode='Markdown')
                self.bot.send_message(message.chat.id, message_text, reply_markup=self.rack2_keyboard,parse_mode='Markdown')
                self.bot.send_message(message.chat.id, "_For now, only the 'Rack #2' available_", reply_markup=self.rack2_keyboard,parse_mode='Markdown')
                


                
            else:
                self.bot.reply_to(message, "Invalid zone selection or not available.")
        # Send localization
        @self.bot.message_handler(func=lambda message: message.text in ["Rack #2","Rack #1","Rack #3"])
        def button_handler(message):
            # Find the location corresponding to the button text
            location_name = message.text

            if location_name == 'Rack #2':
                rack = re.findall(r'\d',message.text)
                #longitude, latitude = self.read_Localization(rack[0])
                latitude = 7.6567050250754525
                longitude  = 45.06480112528298
                # Otherwise, send the location information
                message_text= "*\U0001F6B4 Let's go for that rack, click on the map for directions!*"
                message_text2 ="Leave us your feedback, only 2 min \U0001F91E https://forms.gle/5yW2r5iYNw5VA2cb8"
                
                self.bot.send_message(message.chat.id, message_text, reply_markup=self.rack2_keyboard,parse_mode='Markdown')
                self.bot.send_location(message.chat.id, longitude, latitude, reply_markup=self.rack2_keyboard)
                self.bot.send_message(message.chat.id, message_text2, reply_markup=self.rack2_keyboard,parse_mode='Markdown')
                
            else:
                # If the location wasn't found, send an error message
                self.bot.send_message(message.chat.id, "Invalid selection or not available.")

         # Handle help selection
        @self.bot.message_handler(func=lambda message: message.text in ["Help"])
        def help(message):
            if message.text == "Help":
                message_text = "\U0001F469 *What Smart rack Polito chatbot is?* It is a pilot service that allows you to find and get the localization of a free place for your bike on the Polito campus in real-time or for an estimation of the next 2h. \n"
                message_text += "\U0001F9D1 *How does it work?* Select the area you want to go to, find out about the status of the racks in the area, and select the one that suits you best to get the location on the map.\n"
                message_text += "\U00002139 *At the moment, ONLY the zone 'M and N' with the bike rack 'R2' is AVAILABLE.*\n"
                message_text += "\U0001F4EC If you have any questions or suggestions, please email us at smartrack2022@gmail.com \n"
                message_text += "\U000021AA Write /start to *change language* or *comeback to chat*"
                
                # Send the message using the reply_to method of the bot object
                reply_markup = ReplyKeyboardRemove()
                self.bot.reply_to(message, message_text, reply_markup=reply_markup,parse_mode='Markdown')
                  
            else:
                reply_markup = ReplyKeyboardRemove()
                self.bot.reply_to(message, "Invalid selection or not available.",reply_markup=reply_markup)
                
        # Start the bot
        self.bot.infinity_polling()
        
if __name__ == '__main__':
    bot = SmartRackChatbot("5856399288:AAEUv-kY9oJ1PxLGThO0wviLfp30LNUdblI")
    bot.start()
