# Last update 22.04.23 03:41 

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
        self.rack_keyboard.row(KeyboardButton('R1'), KeyboardButton('R2'), KeyboardButton('R3'))
        self.rack_keyboard.row(KeyboardButton("Select another zone"), KeyboardButton("Help"))
        
        self.rack2_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        self.rack2_keyboard.row(KeyboardButton('R1'), KeyboardButton('R2'), KeyboardButton('R3'))
        self.rack2_keyboard.row(KeyboardButton('Select another zone'),KeyboardButton("Help"))
        
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
    
    def get_message_text(self):
        timezone = pytz.timezone('Europe/Rome')
        now = datetime.datetime.now(timezone)
        message_text="\n"
        for i in self.racks:
            self.rack=i
            print(i)
            message_text += "*R*"+ str(i) + ":\n"
            message_text += "NOW - Free slots (" + now.strftime('%H:%M') + "): " + str(self.read_BikeCount()) + "\n"

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
                message_text += "\n"
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
            self.bot.reply_to(message, "Pick your preferred language:", reply_markup=self.language_keyboard)

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
            with open('zones_byname.png', 'rb') as photo:
                self.bot.send_photo(message.chat.id, photo)
            self.bot.reply_to(message, "From the picture, select the area you are going to:", reply_markup=zone_buttons)
            
        # Handle zone selection
        @self.bot.message_handler(func=lambda message: message.text in self.labels or message.text== "Update this info")
        def process_zone_selection(message):
            # Get the selected zone
            #selected_zone = next((zone for zone in self.locations['features'] if zone['properties']['name'] == message.text), None)
            if message.text == "Aula M-N" or message.text== "Update this info":
                print(" process_zone_selection running: " + message.text)
                # Send the picture of the racks in the zone
                with open('racks.png', 'rb') as photo:
                    self.bot.send_photo(message.chat.id, photo)
                
                message_text = "*State of racks in the zone:*\n"  # Add two newlines to create a gap between the title and the list
                racks = [1,1,1]
                self.racks = racks
                message_text += self.get_message_text()
                button = InlineKeyboardButton("Update this info", callback_data="button_callback")
                # Create the markup with the button
                markup = InlineKeyboardMarkup().add(button)
                
                # Send the message with the markup
                self.bot.send_message(message.chat.id, message_text, reply_markup=markup,parse_mode='Markdown')
                self.bot.send_message(message.chat.id, "Select a rack to get the map localization:", reply_markup=self.rack2_keyboard)


            else:
                self.bot.reply_to(message, "Invalid zone selection or not available.")
        # Send localization
        @self.bot.message_handler(func=lambda message: message.text in ["R1","R2","R3"])
        def button_handler(message):
            # Find the location corresponding to the button text
            location_name = message.text

            if location_name == 'R2':
                rack = re.findall(r'\d',message.text)
                #longitude, latitude = self.read_Localization(rack[0])
                latitude = 7.6567050250754525
                longitude  = 45.06480112528298
                # Otherwise, send the location information
                self.bot.send_location(message.chat.id, longitude, latitude, reply_markup=self.rack2_keyboard)
            else:
                # If the location wasn't found, send an error message
                self.bot.send_message(message.chat.id, "Invalid selection or not available.")

         # Handle help selection
        @self.bot.message_handler(func=lambda message: message.text in ["Help"])
        def help(message):
            if message.text == "Help":
                message_text = "Hey! *Smart rack Polito* is a pilot service that allows you to find a free place for your bike on the Polito campus in real time or within 2 hours of your inquiry.\n"
                message_text += "Select the area you want to go to, find out about the status of the racks in the area, and select the one that suits you best to get the location on the map.\n"
                message_text += "*At the moment, ONLY the zone 'M and N' with the bike rack 'R2' is AVAILABLE.*\n"
                message_text += "If you have any questions or suggestions, please email us at smarrack2022@gmail.com \n"
                message_text += "/start - Change language"
                
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
