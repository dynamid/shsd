from flask import *
from sqlalchemy import *
from sqlalchemy.sql import *
from sqlalchemy.orm import scoped_session, sessionmaker
from manuf import manuf
import datetime
import re
import requests
import time
import geojson

# local imports
from daemon import startBackgoundTasks
from database import *


# engine = create_engine('sqlite:///database.db', echo=False)
# session_factory = sessionmaker(bind=engine)
# Session = scoped_session(session_factory)
#
# metadata = MetaData()
#
# devices = Table('devices', metadata,
#     Column('did', Integer, autoincrement=True, primary_key=True),
#     Column('ip', String),
#     Column('hw', String, unique=True),
# 	Column('manuf', String),
# 	Column('label', String),
# 	Column('firstseen', Date),
# 	Column('lastseen', Date))
#
# services = Table('services', metadata,
# 	Column('sid', Integer, autoincrement=True, primary_key=True),
# 	Column('sname', String, unique=True))
#
# accounts = Table('accounts', metadata,
# 	Column('aid', Integer, autoincrement=True, primary_key=True),
# 	Column('login', String),
# 	Column('sid', Integer),
# 	Column('ip', Integer),
#     Column('ip_org', String),
#     Column('ip_country', String),
#     Column('ip_countrycode', String),
#     Column('ip_city', String),
#     Column('ip_geoloc', String),
# 	Column('firstseen', Date),
#     Column('lastseen', Date))
#
#
#
# metadata.create_all(engine)

now = datetime.datetime.utcnow()

p = manuf.MacParser(update=False)
app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
	return render_template('index.html', devices=getDevices(), connections=getConnections())

@app.route('/api/getDevices')
def getJSONDevices():
	return jsonify(getDevices())


def getDevices():
        s = select([devices])
        mydevices = []
        for row in Session.execute(s):
                mydevices.append({'ip' : row[devices.c.ip],
                                'hw' : row[devices.c.hw],
                                'manuf' : row[devices.c.manuf],
				'firstseen' : row[devices.c.firstseen],
                                'lastseen' : row[devices.c.lastseen],
				'label' : row[devices.c.label]})

        #print(mydevices)
        return mydevices


def getConnections():
        s = select([accounts]).order_by(accounts.c.login)
        myaccounts = []
        for row in Session.execute(s):
                myaccounts.append({'ip' : row[accounts.c.ip],
                                'user' : row[accounts.c.login],
				'firstseen' : row[accounts.c.firstseen],
                                'lastseen' : row[accounts.c.lastseen],
                                'ip_org' : row[accounts.c.ip_org],
                                'ip_city' : row[accounts.c.ip_city]})
        #print(myaccounts)
        return myaccounts



# API

@app.route('/api/addDevice/<ip>/<hw>')
def addDevice(ip, hw):
    now = datetime.datetime.utcnow()
    try:
        Session.execute(devices.insert(), [
            {'ip': ip, 'hw': hw, 'firstseen': now,
            'lastseen': now, 'label': 'none',
            'manuf': p.get_manuf_long(hw)}
            ])
    except:
        Session.execute(devices.update().where(devices.c.hw==hw).values(lastseen=now))
    Session.commit()
    Session.remove()
    return ("device added : " + hw)

@app.route('/api/addConnection/<service>/<ip>/<user>')
def addConnection(ip, user, service):
    now = datetime.datetime.utcnow()
    s = select([accounts.c.login, accounts.c.ip]).where(and_(
                                accounts.c.ip == ip, accounts.c.login == user)).count()
    known = Session.execute(s).scalar()
    print(known)
    if (known == 0):
        if (isLocalIP(ip)):
            Session.execute(accounts.insert(), [
                {'login': user, 'ip': ip, 'firstseen': now, 'lastseen': now, 'ip_org': "LAN"}
                ])
        else:
            onyphe = requests.get("https://www.onyphe.io/api/geoloc/" + ip)
            if (onyphe.status_code == 200 and len(onyphe.json()['results']) > 0):
                print(onyphe.json()['results'][0]['organization'])
                Session.execute(accounts.insert(), [
                    {'login': user, 'ip': ip, 'firstseen': now, 'lastseen': now, 'ip_org': onyphe.json()['results'][0]['organization'],
                    'ip_country': onyphe.json()['results'][0]['country_name'], 'ip_countrycode': onyphe.json()['results'][0]['country'],
                    'ip_city': onyphe.json()['results'][0]['city'], 'ip_geoloc': onyphe.json()['results'][0]['location']}])
            else:
                Session.execute(accounts.insert(), [
                    {'login': user, 'ip': ip, 'firstseen': now, 'lastseen': now}
                ])
    else:
        Session.execute(accounts.update().where(and_(accounts.c.ip == ip, accounts.c.login == user)).values(lastseen=now))
    Session.commit()
    Session.remove()
    return ("connection added : " + user)

def isLocalIP(ip):
    return (ip.startswith("192.168.") or ip.startswith("172.16.") or ip.startswith("10."))

@app.route('/api/getGeoJSON/<user>')
def getGeoJSON(user):
	mygeojson = geojson.Point((-115.81, 37.24))
	return (geojson.dumps(mygeojson, sort_keys=True))


if __name__ == '__main__':
    startBackgoundTasks()
    app.run(debug=True)
