from bs4 import BeautifulSoup as bs
import requests
import os
import pathlib
import datetime
import time
import configparser
#needs to be executed first
runPath = pathlib.Path(__file__).parent.absolute()
os.chdir(runPath)

config = configparser.ConfigParser()
config.read("config.ini")

chat_id = config["botdata"]["chat_id"]
token = config["botdata"]["token"]
timeBetweenCurls = config["botdata"]["timeBetweenCurls"]
url= "https://api.telegram.org/bot" + token + "/sendMessage"

messageData = {
    "chat_id":chat_id,
    "text":"LOLOLOLOLO"
}
lastUpdateDate = "lastupdate.txt"
lastupdate=""
if(not os.path.exists(lastUpdateDate)):
    open(lastUpdateDate, "x").write("01.01.1990")
with open(lastUpdateDate,"r") as f:
    lastupdate = f.readline().replace(" ","").replace("\n","")
print(lastupdate)
nichtDurch = True
tries = 0
maxTries = 24
while(nichtDurch and tries<maxTries):
    if(datetime.datetime.strptime(lastupdate, '%d.%m.%Y').date()!=datetime.datetime.now().date() and datetime.datetime.now().hour>10):
        tries+=1
        data = requests.get('https://www.aachen.de/DE/stadt_buerger/notfall_informationen/corona/aktuelles/index.html')
        soup = bs(data.text,'html.parser')
        aTables = soup.findAll("table")
        for table in aTables:
            if(len(table.findAll("tr"))==3):
                trs = table.findAll("tr")
                for tr in trs:
                    tds = tr.findAll("td")
                    if ("RKI-Inzidenz" in tds[0].get_text()):
                        datum = trs[1].findAll("td")
                        datum = datum[len(datum)-1].find("div").get_text().replace("21","2021")
                        message = "Aktuelle Inzidenz am " + datum +": "+ tds[len(tds)-1].find("div").get_text()
                        print(message)
                        messageData["text"]=message
                        requests.get(url,data=messageData)
                        open(lastUpdateDate,"w").write(datum)
                        nichtDurch=False
        if(nichtDurch):
            time.sleep(timeBetweenCurls)
    else:
        nichtDurch=False
