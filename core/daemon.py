import threading
from sqlalchemy.sql import *
import time
import requests
import random
from flask import *

from database import *

onyphe_mylocation = None
Session = None

def isLocalIP(ip):
    return (ip.startswith("192.168.") or ip.startswith("172.16.") or ip.startswith("10.") or ip.startswith("127."))

def updateIPInfo():
    #print("Updating IP Info")
    global Session
    s = select([accounts]).where(accounts.c.is_populated == False)
    for row in Session.execute(s):
        print('Updating ' + row[accounts.c.ip])
        if (isLocalIP(row[accounts.c.ip])):
            global onyphe_mylocation
            if (onyphe_mylocation == None):
                onyphe_myip = requests.get("https://www.onyphe.io/api/myip")
                if (onyphe_myip.status_code == 200 and len(onyphe_myip.json()['myip']) > 0):
                    myip = onyphe_myip.json()['myip']
                    onyphe_mylocation = requests.get("https://www.onyphe.io/api/geoloc/" + myip)
            if (onyphe_mylocation != None and onyphe_mylocation.status_code == 200 and len(onyphe_mylocation.json()['results']) > 0):
                Session.execute(accounts.update().where(
                            and_(accounts.c.ip == row[accounts.c.ip], accounts.c.login == row[accounts.c.login])).values(
                            ip_org = "LAN",
                            ip_longitude= onyphe_mylocation.json()['results'][0]['longitude'],
           				    ip_latitude= onyphe_mylocation.json()['results'][0]['latitude'],
                            ip_as=onyphe_mylocation.json()['results'][0]['asn'],
                            ip_country=onyphe_mylocation.json()['results'][0]['country_name'],
                            ip_countrycode=onyphe_mylocation.json()['results'][0]['country'],
                            ip_city=onyphe_mylocation.json()['results'][0]['city'],
                            is_populated = True))
        else:
            onyphe = requests.get("https://www.onyphe.io/api/geoloc/" + row[accounts.c.ip])
            if (onyphe.status_code == 200 and len(onyphe.json()['results']) > 0):
                Session.execute(accounts.update().where(
                        and_(accounts.c.ip == row[accounts.c.ip], accounts.c.login == row[accounts.c.login])).values(
                                ip_org=onyphe.json()['results'][0]['organization'],
                                ip_country=onyphe.json()['results'][0]['country_name'],
                                ip_countrycode=onyphe.json()['results'][0]['country'],
                                ip_city=onyphe.json()['results'][0]['city'],
                                ip_longitude=onyphe.json()['results'][0]['longitude'],
                                ip_latitude=onyphe.json()['results'][0]['latitude'],
                                ip_as=onyphe.json()['results'][0]['asn'],
                                is_populated=True))
            else:
                print("Rate limited on onyphe")
                # try/catch a ajouter
                # try:
                #     Session.commit()
                # except:
                #     Session.rollback()
                # t = threading.Timer(60 + random.randint(2,10), updateIPInfo)
                # t.daemon = True
                # t.start()
                break
    try:
        Session.commit()
    except:
        Session.rollback()
    Session.remove()

def updateIPInfoDaemon():
    while(True):
        try :
            time.sleep(2)
            updateIPInfo()
            #requests.get(url_for('populateIpInfo', _external=True))
            time.sleep(60 + random.randint(2,10))
        except:
            pass


def startBackgoundTasks(mySession):
    global Session
    Session = mySession
    IPInfoUpdater = threading.Thread(target=updateIPInfoDaemon)
    IPInfoUpdater.daemon = True
    IPInfoUpdater.start()
