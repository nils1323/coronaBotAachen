import requests
import os
import pathlib
import  pytz
import datetime as rootdatetime
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

def start(update, context) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Ein kleiner Bot um sich regelmäßig die aktuellen Inzidenzen anzeigen zu lassen.")

def sendTimedUpdate(contextlocal):
    chat_id = str(contextlocal.job.context)
    print("HELLOBELLO "+ chat_id)
    logging.info("Sending timed message to "+ chat_id)
    reply= ""
    if chat_id in updater.dispatcher.bot_data:
        reply = buildNotificationString(chat_id)
    if reply == "Es stehen keine Bezirke auf deiner Liste.":
        logging.info("Es stehen keine Bezirke auf der Liste. Evtl sollte die Job-queue mal wieder geleert werden")
    else:
        updater.bot.send_message(chat_id=chat_id, text=reply)
        logging.debug("successfully send message to: " + chat_id)

def register(update, context):
    #context.bot.send_message(chat_id=update.effective_chat.id, text="You did successfully register.")
    firstname = update.effective_user["first_name"]
    chat_id = str(update.message.chat_id)
    print(context.args)
    if len(context.args) == 0 or not context.args[0].isnumeric() or int(context.args[0])>23:
        update.message.reply_text("Hey, bitte schreibe /register [Zeitpunkt als HH oder H] (Zahl zwischen 0 und 23) um zu einem bestimmten Zeitpunkt benachrichtigt zu werden.")
    elif not str(update.message.chat_id) in context.bot_data:
        update.message.reply_text("Hey, bitte füge zuerst einen Ort zu deiner Abo-Liste hinzu.")
    else:
        current_jobs = context.job_queue.get_jobs_by_name(chat_id)
        if current_jobs:
            #a Job exists, remove it and replace it with a new one
            print(updater.job_queue.get_jobs_by_name(chat_id)[0].schedule_removal())
            update.message.reply_text("Moin, deine alte getimte Nachricht wurde durch die Neue ersetzt.")
        key = "job"+chat_id
        h = int(context.args[0])
        updater.dispatcher.bot_data[key]= {"hour":h, "chat_id":chat_id}
        min = 0
        updater.job_queue.run_daily(sendTimedUpdate, rootdatetime.time(hour=h, minute=min, tzinfo=pytz.timezone('Europe/Berlin')), days=(0,1,2,3,4,5,6), context=update.message.chat_id, name=chat_id)
        update.message.reply_text("Erfolgreich eine Benachrichtigung für jeden Tag um " + str(h) + " Uhr"  + " erstellt.")
    # https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/timerbot.py
    logging.debug("current job-queue: " + str(context.job_queue.get_jobs_by_name(chat_id)))

def unregister(update, context):
    chat_id = str(update.message.chat_id)
    print(updater.job_queue.get_jobs_by_name(chat_id)[0].schedule_removal())

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
    reply = ""
    if len(context.args)>0 and len(context.args)<2 and context.args[0].isNumeric():
        value = context.args[0]
        if value in context.bot_data[str(update.message.chat_id)]:
            context.bot_data[str(update.message.chat_id)].remove(value)
            reply = inv_districts[value] + " successfully removed."
        else:
            reply = value + " ist nicht auf deiner Liste. du kannst dir deine Liste mit /list anzeigen lassen."
    else:
        reply = "Bitte gib eine Distriktnummer an :)"
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
    # one-time notification called with /notify
    chat_id = str(update.message.chat_id)
    reply = buildNotificationString(chat_id)
    update.message.reply_text(reply)

def buildNotificationString(chat_id:str)-> str:
    global updater
    reply = ""
    updateIncidences()
    if chat_id in updater.dispatcher.bot_data and len(updater.dispatcher.bot_data[chat_id])>0:
        datumOfIncidences = str(datetime.strptime(cachedincidences["meta"]["lastUpdate"],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc).astimezone(tz=None).date())
        reply = "Am " + str(datumOfIncidences) + " betragen die Inzidenzen in deinen abonnierten Bezirken die folgenden Werte:\n"
        for bezirknr in updater.dispatcher.bot_data[chat_id]:
            reply = reply +inv_districts[bezirknr] + ": {0:0.1f}\n".format(cachedincidences["data"][bezirknr]["weekIncidence"])
    else: 
        reply = "Es stehen keine Bezirke auf deiner Liste."
    return reply

def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

def restoreJobs():
    logging.info("Current Jobs " + str(updater.dispatcher.bot_data.keys()))
    for key in updater.dispatcher.bot_data.keys():
        if "job" in str(key):
            h=int(updater.dispatcher.bot_data[key]["hour"])
            min = 0
            chat_id = updater.dispatcher.bot_data[key]["chat_id"]
            updater.job_queue.run_daily(sendTimedUpdate, rootdatetime.time(hour=h, minute=min, tzinfo=pytz.timezone('Europe/Berlin')), days=(0,1,2,3,4,5,6), context=chat_id, name=chat_id)


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
    if isinstance(chat_id,int):
        fixedDict.pop(chat_id,None)
dispatcher.bot_data.update(fixedDict)

restoreJobs()

#updater.dispatcher.job_queue.run_daily()
updater.start_polling()
updater.idle()
exit()