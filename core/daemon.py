import threading
from manuf import manuf
from sqlalchemy.sql import *
import time
import requests
import random
from flask import *


from database import *

def isLocalIP(ip):
    return (ip.startswith("192.168.") or ip.startswith("172.16.") or ip.startswith("10.") or ip.startswith("127."))

def updateIPInfo():
    print("Updating IP Info")
    s = select([accounts]).where(accounts.c.is_populated == False)
    for row in Session.execute(s):
        print('Updating ' + row[accounts.c.ip])
        if (isLocalIP(row[accounts.c.ip])):
            Session.execute(accounts.update().where(
                            and_(accounts.c.ip == row[accounts.c.ip], accounts.c.login == row[accounts.c.login])).values(
                            ip_org = "LAN",
                            is_populated = True)
        else:
            onyphe = requests.get("https://www.onyphe.io/api/geoloc/" + row[accounts.c.ip])
            if (onyphe.status_code == 200 and len(onyphe.json()['results']) > 0):
                print(onyphe.json()['results'][0]['organization'])
                Session.execute(accounts.update().where(
                        and_(accounts.c.ip == row[accounts.c.ip], accounts.c.login == row[accounts.c.login])).values(
                                ip_org=onyphe.json()['results'][0]['organization'],
                                ip_country=onyphe.json()['results'][0]['country_name'],
                                ip_countrycode=onyphe.json()['results'][0]['country'],
                                ip_city=onyphe.json()['results'][0]['city'],
                                ip_longitude=onyphe.json()['results'][0]['longitude'],
                                ip_latitude=onyphe.json()['results'][0]['latitude'],
                                is_populated=True))
            else:
                print("Rate limited on onyphe")
                # try/catch a ajouter
                Session.commit()
                t = threading.Timer(60 + random.randint(2,10), updateIPInfo)
                t.daemon = True
                t.start()
                break
    Session.commit()
    Session.remove()

def updateIPInfoDaemon():
    while(True):
        time.sleep(random.randint(2,10))
        updateIPInfo()
        #requests.get(url_for('populateIpInfo', _external=True))
        time.sleep(60 + random.randint(2,10))


def startBackgoundTasks():
    IPInfoUpdater = threading.Thread(target=updateIPInfo)
    IPInfoUpdater.daemon = True
    IPInfoUpdater.start()
