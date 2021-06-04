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
#needs to be executed first
runPath = pathlib.Path(__file__).parent.absolute()
os.chdir(runPath)
config = configparser.ConfigParser()
config.read("config.ini")

chat_id = config["botdata"]["chat_id"]
token = config["botdata"]["token"]

url= "https://api.telegram.org/bot" + token + "/sendMessage"

def send(message):
    messageData = {
        "chat_id":chat_id,
        "text":message
    }

    requests.get(url,data=messageData)


data = requests.get("https://api.corona-zahlen.org/districts")
jsonObject = json.loads(data.content)
datum = str(datetime.strptime(jsonObject["meta"]["lastUpdate"],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc).astimezone(tz=None).date())
lastUpdated = str(datetime.strptime(jsonObject["meta"]["lastCheckedForUpdate"],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc).astimezone(tz=None).time().replace(microsecond=0))
print(datum)
incidenceAachen = str(jsonObject["data"]["05334"]["weekIncidence"])
incidenceBorken = str(jsonObject["data"]["05554"]["weekIncidence"])
send("Inzidenzen vom " + datum + " zuletzt um " + lastUpdated + " überprüft.\nAachen: " + incidenceAachen + "\nBorken: " + incidenceBorken)

