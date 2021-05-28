from bs4 import BeautifulSoup as bs
import requests
import os
import pathlib
import datetime
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
timeBetweenCurls = 60#int(config["botdata"]["timeBetweenCurls"])
url= "https://api.telegram.org/bot" + token + "/sendMessage"

messageData = {
    "chat_id":chat_id,
    "text":"LOLOLOLOLO"
}
lastUpdateDate = "lastupdate.txt"
lastupdate=""
if(not os.path.exists(lastUpdateDate)):
    open(lastUpdateDate, "x").write("2021-05-20")
with open(lastUpdateDate,"r") as f:
    lastupdate = f.readline().replace(" ","").replace("\n","")
print(lastupdate)
nichtDurch = True
tries = 0
maxTries = 180

while(nichtDurch and tries<maxTries):
    if(datetime.datetime.strptime(lastupdate,'%Y-%m-%d').date()!=datetime.datetime.now().date()):
        tries+=1
        data = requests.get("https://api.corona-zahlen.org/districts")
        jsonObject = json.loads(data.content) 
        datum = str(datetime.datetime.strptime(jsonObject["meta"]["lastUpdate"],'%Y-%m-%dT%H:%M:%S.%fZ').date())
        print(datum)
        if(str(datetime.datetime.now().date()) in datum ):#datetime.datetime.now().date()):
            incidenceAachen = str(jsonObject["data"]["05334"]["weekIncidence"])
            incidenceHagen = str(jsonObject["data"]["05914"]["weekIncidence"])
            message = "Die Aktuellen Inzidenzen vom " + datum + " sind für\nAachen: " +incidenceAachen + "\nHagen: " + incidenceHagen
            messageData["text"]=message
            requests.get(url,data=messageData)
            open(lastUpdateDate,"w").write(datum)
            nichtDurch=False
        if(nichtDurch):
            time.sleep(timeBetweenCurls)
    else:
        nichtDurch=False
