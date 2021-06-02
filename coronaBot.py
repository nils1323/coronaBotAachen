import requests
import os
import pathlib
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import time
import configparser
import json
from telegram.ext import Updater
import logging
from telegram.ext import MessageHandler, Filters
from telegram.ext import CommandHandler
from telegram.ext.picklepersistence import PicklePersistence
import sys


#chat_ids = config["botdata"]["chat_id"].split(",")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
cachedincidences = ""
lastcached = ""

def updateIncidences():
    global cachedincidences, lastcached
    if (cachedincidences == "" and lastcached == ""):
        data = requests.get("https://api.corona-zahlen.org/districts")
        cachedincidences = json.loads(data.content)
        lastcached = datetime.now()
        logging.info("Updated incidences cause of none existend")
    elif (datetime.now() - lastcached).total_seconds() / 60.0 > 15:
        data = requests.get("https://api.corona-zahlen.org/districts")
        cachedincidences = json.loads(data.content)
        lastcached = datetime.now()
        logging.info("Updated Incidences cause of timediff")


def renewDistrict():
    try:
        if not os.path.exists(districtCacheFileName):
            open(districtCacheFileName,"x").close()
        with open(districtCacheFileName, "w") as f:
            data = requests.get("https://api.corona-zahlen.org/districts")
            jsonObject = json.loads(data.content)
            dicts = jsonObject["data"]
            newDict = {}
            for dict2 in dicts:
                newDict[dicts[dict2]["name"]] = dicts[dict2]["ags"]
            f.write(str(newDict))
    except:
        os.remove(districtCacheFileName)
        print(sys.exc_info(), " in renewDistrict")

def writeConfig():
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def getTime(hour) -> datetime.time:
    if(len(str(hour))==1):
        hour = "0".join(str(hour))
    time = datetime.strptime(str(hour),"%H")
    print(time.time())

def start(update, context) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Ein kleiner Bot um sich regelmäßig die aktuellen Inzidenzen anzeigen zu lassen.")

def sendTimedUpdate(contextlocal):
    global updater
    chat_id = str(contextlocal.job.context)
    if not str(chat_id) in updater.dispatcher.bot_data:
        print("")

def register(update, context):
    #context.bot.send_message(chat_id=update.effective_chat.id, text="You did successfully register.")
    firstname = update.effective_user["first_name"]
    print(context.args)
    if len(context.args) == 0 or not context.args[0].isnumeric() or int(context.args[0])>23:
        update.message.reply_text("Hey, bitte schreibe /register [Zeitpunkt als HH oder H] (Zahl zwischen 0 und 23) um zu einem bestimmten Zeitpunkt benachrichtigt zu werden.")
    elif not str(update.message.chat_id) in context.bot_data:
        update.message.reply_text("Hey, bitte füge zuerst einen Ort zu deiner Abo-Liste hinzu.")
    else:
        current_jobs = context.job_queue.get_jobs_by_name(update.effective_chat.id)
        if current_jobs:
            update.message.reply_text("Moin, du kannst hast schon eine getimte Nachricht. Der Einfachheit halber, ist nur eine möglich.")
        else:
            context.job_queue.run_daily(sendTimedUpdate, getTime(context.args[0]), days=(0,1,2,3,4,5,6), context=update.message.chat_id)
            update.message.reply_text("Erfolgreich eine Benachrichtigung für jeden Tag um " + str(getTime(context.args[0]))+ " erstellt.")
            print(getTime(context.args[0]))
            print(firstname)
    # https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/timerbot.py

def unregister(update, context):
    print("abcd")

def search(update, context):
    # search district, to get district number Use cached list
    args= context.args
    if len(args) == 0:
        update.message.reply_text("Du musst irgendeinen Suchbegriff eingeben.")
    else:
        suchbegriff = ""
        logging.debug("searched for " + str(args))
        for begriff in args:
            suchbegriff =suchbegriff+" " + begriff
        suchbegriff = suchbegriff[1:]
        if len(suchbegriff)<3:
            update.message.reply_text("Bitte gib mindestens 3 Zeichen ein")
        elif len(suchbegriff)>50:
            update.message.reply_text("Alter.... jetzt troll doch nicht....")
        else:
            result = []
            for district in districts:
                if suchbegriff.upper() in district.upper():
                    result.append((district, districts[district]))
            if len(result) == 0:
                update.message.reply_text("Es wurden keine Bezirke mit diesem Namen gefunden.")
            else:
                reply="Die folgenden Bezirke wurden gefunden\(kopieren durch klicken geht nur auf Smartphones\):\n"
                for district in result:
                    name,number = district  
                    reply = reply+ str(name).replace("-","\-").replace(".", "\.") +r" mit Nummer `" +"/add " + str(number) + r"` wurde gefunden\." + "\n"
                reply = reply + ""
                update.message.reply_text(reply, parse_mode='MarkdownV2')

#Adds a district to notification klist
def add(update, context):
    reply = ""
    if context.args[0] in districts.values():
        try: 
            len(context.bot_data[str(update.message.chat_id)])
        except:
            logging.info("No dict for" + str(update.message.chat_id) + " available. Creating one")
            context.bot_data[str(update.message.chat_id)] = [context.args[0]]
            #{"0": context.args[0]}
            reply = inv_districts[context.args[0]]+" wurde erfolgreich zu deiner Benachrichtigungsliste hinzugefügt."
        else: 
            if context.args[0] in context.bot_data[str(update.message.chat_id)]:
                reply = inv_districts[context.args[0]] + " steht bereits auf deiner Liste und kann deshalb nicht hinzugefügt werden."
            else:
                context.bot_data[str(update.message.chat_id)].append(context.args[0])
                reply = inv_districts[context.args[0]]+" wurde erfolgreich zu deiner Benachrichtigungsliste hinzugefügt."
    else:
        reply = "Ist keine valide Bezirksnummer."
    update.message.reply_text(reply)

# remvoe a district from notification list
def remove(update, context):
    value = context.args[0]
    reply = ""
    if value in context.bot_data[str(update.message.chat_id)]:
        context.bot_data[str(update.message.chat_id)].remove(value)
        reply = inv_districts[value] + " successfully removed."
    else:
        reply = value + " ist nicht auf deiner Liste. du kannst dir deine Liste mit /list anzeigen lassen."
    logging.debug(context.bot_data[str(update.message.chat_id)])
    update.message.reply_text(reply)

def listf(update, context):
    reply = "Die folgenden Bezirke stehen auf deiner Liste:\n"
    try: 
        len(context.bot_data[str(update.message.chat_id)])
    except:
        reply = "Es stehen keine Bezirke auf deiner Liste."
    else:
        for bezirknr in context.bot_data[str(update.message.chat_id)]:
            reply = reply + inv_districts[bezirknr] + " mit Nummer " + bezirknr + ".\n" 
    update.message.reply_text(reply)

def notify(update, context):
    updateIncidences()
    # one-time notification
    reply = ""
    try: 
        len(context.bot_data[str(update.message.chat_id)])
    except:
        reply = "Es stehen keine Bezirke auf deiner Liste."
    else:
        datumOfIncidences = str(datetime.strptime(cachedincidences["meta"]["lastUpdate"],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc).astimezone(tz=None).date())
        reply = "Am " + str(datumOfIncidences) + " betragen die Inzidenzen in deinen abonnierten Bezirken die folgenden Werte:\n"
        for bezirknr in context.bot_data[str(update.message.chat_id)]:
            reply = reply +inv_districts[bezirknr] + ": {0:0.1f}\n".format(cachedincidences["data"][bezirknr]["weekIncidence"])
    update.message.reply_text(reply)

def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

#needs to be executed first changes directory to the path of this file
runPath = pathlib.Path(__file__).parent.absolute()
os.chdir(runPath)
config = configparser.ConfigParser()
config.read("config.ini")
my_persistence = PicklePersistence(filename='persistent_data.save')
districtCacheFileName = "districts.cache"

token = config["botdata"]["token"]

updater = Updater(token=token, persistence=my_persistence, use_context=True)
dispatcher = updater.dispatcher


#Check if district are already cached and cache them if neccessary
if not os.path.exists(districtCacheFileName):
    renewDistrict()
districts = eval(open(districtCacheFileName,"r").read())
inv_districts = {v: k for k, v in districts.items()}


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

register_handler = CommandHandler("register",register, pass_job_queue=True)
dispatcher.add_handler(register_handler)

search_handler = CommandHandler("search",search)
dispatcher.add_handler(search_handler)

add_handler = CommandHandler("add",add)
dispatcher.add_handler(add_handler)

remove_handler = CommandHandler("remove",remove)
dispatcher.add_handler(remove_handler)

notify_handler = CommandHandler("notify",notify)
dispatcher.add_handler(notify_handler)

list_handler = CommandHandler("list",listf)
dispatcher.add_handler(list_handler)

unregister_handler = CommandHandler("unregister",unregister, pass_job_queue=True)
dispatcher.add_handler(unregister_handler)

#Last Command
unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)


#adjust old keys to new format
fixedDict={}
for chat_id in dispatcher.bot_data:
    fixedDict[str(chat_id)] = dispatcher.bot_data[chat_id]
dispatcher.bot_data.update(fixedDict)

#updater.dispatcher.job_queue.run_daily()
updater.start_polling()
exit()