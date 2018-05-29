import threading
from manuf import manuf
from sqlalchemy.sql import *
import time
import requests

from database import *



def updateIPInfo():
    while(True):
        print("Updating IP Info")
        s = select([accounts]).where(accounts.c.ip_org == None)
        for row in Session.execute(s):
            print('Updating ' + row[accounts.c.ip])
            onyphe = requests.get("https://www.onyphe.io/api/geoloc/" + row[accounts.c.ip])
            if (onyphe.status_code == 200 and len(onyphe.json()['results']) > 0):
                print(onyphe.json()['results'][0]['organization'])
                Session.execute(accounts.update().where(
                        and_(accounts.c.ip == row[accounts.c.ip], accounts.c.login == row[accounts.c.login])).values(
                                ip_org=onyphe.json()['results'][0]['organization'],
                                ip_country=onyphe.json()['results'][0]['country_name'],
                                ip_countrycode=onyphe.json()['results'][0]['country'],
                                ip_city=onyphe.json()['results'][0]['city'],
                                ip_geoloc=onyphe.json()['results'][0]['location'],
                                ip_longitude=onyphe.json()['results'][0]['longitude'],
                                ip_latitude=onyphe.json()['results'][0]['latitude']))
        Session.commit()
        Session.remove()
        time.sleep(60)


def startBackgoundTasks():
    IPInfoUpdater = threading.Thread(target=updateIPInfo)
    IPInfoUpdater.daemon = True
    IPInfoUpdater.start()
