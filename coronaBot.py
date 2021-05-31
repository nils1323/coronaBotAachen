import zoneinfo
from bs4 import BeautifulSoup as bs
import requests
import os
import pathlib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import time
import configparser
import json
from telegram.ext import Updater
import logging
from telegram.ext import MessageHandler, Filters
from telegram.ext import CommandHandler
from telegram.ext.picklepersistence import PicklePersistence

#needs to be executed first
runPath = pathlib.Path(__file__).parent.absolute()
os.chdir(runPath)
config = configparser.ConfigParser()
config.read("config.ini")
my_persistence = PicklePersistence(filename='persistent_data.save')

chat_ids = config["botdata"]["chat_id"].split(",")
token = config["botdata"]["token"]

updater = Updater(token=token, persistence=my_persistence, use_context=True)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

def writeConfig():
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Ein kleiner Bot um sich regelmäßig die aktuellen Inzidenzen anzeigen zu lassen.")

def register(update, context):
    #context.bot.send_message(chat_id=update.effective_chat.id, text="You did successfully register.")
    firstname = update.effective_user["first_name"]
    if len(context.args) == 0:
        update.message.reply_text("Hey, ", firstname , " bitte schreibe \\register [Zeitpunkt] um zu einem bestimmten Zeitpunkt benachrichtigt zu werden.")
        
    print(context.args)
    print(firstname)
    # https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/timerbot.py

def search(update, context):
    # search district, to get district number Use cached list
    print("TODO")
    #TODO

def add(update, context):
    # add a district to notification list
    #TODO
    print("TODO")

def remove(update, context):
    # remvoe a district from notification list
    #TODO
    print("TODO")

def notify(update, context):
    # one-time notification
    #TODO
    print("TODO")

def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

register_handler = CommandHandler("register",register)
dispatcher.add_handler(register_handler)

search_handler = CommandHandler("search",search)
dispatcher.add_handler(search_handler)

add_handler = CommandHandler("add",add)
dispatcher.add_handler(add_handler)

#Last Command
unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

updater.start_polling()
exit()

url= "https://api.telegram.org/bot" + token + "/sendMessage"


def send(message,chat_id):
    for chat_id in chat_ids:
        messageData = {
            "chat_id":chat_id,
            "text":message
        }
        response = requests.get(url,data=messageData)
        print(response)
        time.sleep(1)

def writeConfig():
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def sendHelp(chat_id):
    send(helpString,chat_id)
    


data = requests.get("https://api.corona-zahlen.org/districts")
jsonObject = json.loads(data.content)
datum = str(datetime.strptime(jsonObject["meta"]["lastUpdate"],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc).astimezone(tz=None).date())
lastUpdated = str(datetime.strptime(jsonObject["meta"]["lastCheckedForUpdate"],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc).astimezone(tz=None).time().replace(microsecond=0))
print(datum)
incidenceAachen = str(jsonObject["data"]["05334"]["weekIncidence"])
incidenceHagen = str(jsonObject["data"]["05914"]["weekIncidence"])
incidenceBorken = str(jsonObject["data"]["05554"]["weekIncidence"])
for chat_id in chat_ids:
    send("Inzidenzen vom " + datum + " zuletzt um " + lastUpdated + " überprüft.\nAachen: " + incidenceAachen + "\nHagen: " + incidenceHagen + "\nBorken: " + incidenceBorken,chat_id)

