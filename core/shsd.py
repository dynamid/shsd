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
import threading

# local imports
from daemon import startBackgoundTasks, updateIPInfo
from database import *


now = datetime.datetime.utcnow()

p = manuf.MacParser(update=False)
app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
	return render_template('index.html', devices=getDevices(), connections=getConnections(), center_map=getAvgPositions())

@app.route('/details')
def details():
	return render_template('details.html', devices=getDevices(), connections=getConnections())


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
                {'login': user, 'ip': ip, 'firstseen': now, 'lastseen': now, 'ip_org': "LAN", 'is_populated': True}
                ])
        else:
            onyphe = requests.get("https://www.onyphe.io/api/geoloc/" + ip)
            if (onyphe.status_code == 200 and len(onyphe.json()['results']) > 0):
                print(onyphe.json()['results'][0]['organization'])
                Session.execute(accounts.insert(), [
                    {'login': user, 'ip': ip, 'firstseen': now, 'lastseen': now, 'ip_org': onyphe.json()['results'][0]['organization'],
                    'ip_country': onyphe.json()['results'][0]['country_name'], 'ip_countrycode': onyphe.json()['results'][0]['country'],
                    'ip_city': onyphe.json()['results'][0]['city'],
					'ip_longitude': onyphe.json()['results'][0]['longitude'],
					'ip_latitude': onyphe.json()['results'][0]['latitude'],
					'is_populated': True}])
            else:
                Session.execute(accounts.insert(), [
                    {'login': user, 'ip': ip, 'firstseen': now, 'lastseen': now}
                ])
    else:
        Session.execute(accounts.update().where(and_(accounts.c.ip == ip, accounts.c.login == user)).values(lastseen=now))
    Session.commit()
    Session.remove()
    return ("connection added : " + user)

@app.route('/api/addConnectionJSON', methods=['POST'])
def addConnectionJSON():
	if not request.json:
		abort(400)
	content = json.loads(request.get_json(force=True))
	service = content['service']
	connections = content['connections']
	for connection in connections:
		date = datetime.date(int(connection['year']),int(connection['month']),int(connection['day']))
		ip = connection['ip']
		user = connection['user']
		s = select([accounts.c.login, accounts.c.ip, accounts.c.lastseen]).where(and_(
		               accounts.c.ip == ip, accounts.c.login == user)).count()
		known = Session.execute(s).scalar()
		if (known == 0):
			Session.execute(accounts.insert(), [
		                {'login': user, 'ip': ip, 'firstseen': date, 'lastseen': date, 'is_populated': False}
		           ])
		else:
			s = select([accounts.c.login, accounts.c.ip, accounts.c.lastseen]).where(and_(
					accounts.c.ip == ip, accounts.c.login == user))
			for row in Session.execute(s):
				olddate = row[accounts.c.lastseen]
				if (date > olddate):
					Session.execute(accounts.update().where(and_(accounts.c.ip == ip, accounts.c.login == user)).values(lastseen=date))
	Session.commit()
	Session.remove()
	#threading.Thread(target=updateIPInfo).start()
	startBackgoundTasks()
	return("JSON ok")

def isLocalIP(ip):
    return (ip.startswith("192.168.") or ip.startswith("172.16.") or ip.startswith("10.") or ip.startswith("127."))
#ajouter dynamiquement les markers sur la map
@app.route('/api/getGeoJSON/<user>')
def getGeoJSON(user):
	my_feature = []
	s = select([accounts.c.ip_longitude,accounts.c.ip_latitude,accounts.c.ip]).where(accounts.c.login == user)
	for row in Session.execute(s):
		print(row[accounts.c.ip_latitude])
		print(row[accounts.c.ip_longitude])
		if (row[accounts.c.ip_longitude] != None and row[accounts.c.ip_latitude] != None) :
			my_feature.append(geojson.Feature(geometry=geojson.Point((row[accounts.c.ip_longitude], row[accounts.c.ip_latitude])),
			properties={
	"marker-color": "#0000ff",
	"marker-size": "medium",
	"marker-symbol": "telephone",
	"description": "ip is : " + row[accounts.c.ip]
	}))

# 		#else : my_feature.append(geojson.Feature(geometry=geojson.Point((1, 2)),
# 		properties={
# "marker-color": "#0000ff",
# "marker-size": "medium",
# "marker-symbol": "car",
# "description": "test pour affichage"
# }))
	mygeojson = geojson.FeatureCollection(my_feature)
	return (geojson.dumps(mygeojson, sort_keys=True))

#moyenne des latitude et longitude
def getAvgPositions():
	pos = []
	s = select([func.avg(accounts.c.ip_longitude),func.avg(accounts.c.ip_latitude)]).distinct()
	for row in Session.execute(s):
		pos.append(row[0])
		pos.append(row[1])

	return pos



if __name__ == '__main__':
	startBackgoundTasks() #url_for('populateIpInfo'))
	app.run(debug=False)
