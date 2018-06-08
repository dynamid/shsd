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
import collections
import threading
from random import *


# local imports
from daemon import startBackgoundTasks, updateIPInfo
from database import *


now = datetime.datetime.utcnow()

p = manuf.MacParser(update=False)
app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
	return render_template('index.html', devices=getDevices(), connections=getConnections(), center_map=getAvgPositions(),
	colors = color_aslist, orgs = org_aslist)

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
	#startBackgoundTasks()
	return("JSON ok")

#ajouter dynamiquement les markers sur la map
@app.route('/api/getGeoJSON/<user>')
def getGeoJSON(user):
	my_feature = []
	s = select([accounts.c.ip_longitude,accounts.c.ip_latitude,
	accounts.c.ip_org,accounts.c.ip,accounts.c.ip_as]).where(accounts.c.login == user).distinct()
	as_list = []
	is_in_aslist = False
	as_index = 0
	as_color = 0
	as_org = ' '

	for row in Session.execute(s):
# couleur des markers selon AS

#Taille des markers selon la durée de présence dans la base
		if row[accounts.c.ip_org] == "LAN":
			print("LAAAAN")
			my_feature.append(geojson.Feature(geometry=geojson.Point((row[accounts.c.ip_longitude],
			row[accounts.c.ip_latitude])),
				properties={
		"marker-color": as_color,
		"marker-size": "medium",
		"marker-symbol": "village",
		"description": "ip LAN is : " + row[accounts.c.ip]
		}))

		else :
			my_feature.append(geojson.Feature(geometry=geojson.Point((row[accounts.c.ip_longitude],
			row[accounts.c.ip_latitude])),
			properties={
		"marker-color": as_color,
		"marker-size": "medium",
		"marker-symbol": "marker",
		"description": "ip is : " + row[accounts.c.ip] + " org : " + row[2]
		}))

	print(org_aslist)
	print(as_list)
	print(color_aslist)

	mygeojson = geojson.FeatureCollection(my_feature)

	return (geojson.dumps(mygeojson, sort_keys=True))

#moyenne des latitude et longitude
def getAvgPositions():
	pos = []
	s = select([func.avg(accounts.c.ip_latitude),func.avg(accounts.c.ip_longitude)]).distinct()
	for row in Session.execute(s):
		pos.append(row[0])
		pos.append(row[1])

	return pos

color_aslist = ["#ff0000","#fff700","#1ffd00","#0307fd","#fc03b8","#fc5202","#01fcb4","#9603fc","#ff026a","#ca9d03"]
org_aslist = []
#Générer une nouvelle couleur
# def newColor():
#     hexa = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
#     col = sample(hexa,6)
#     for i in color_aslist: #on vérifie que la couleur n'est pas déjà attribuée
#         if col == i:
#             col = sample(hexa,6)
#
#     color1 = ''.join(col)
#     prefix = '#'
#     color = prefix+color1
#     color_aslist.append(color)
#     return color


if __name__ == '__main__':
	startBackgoundTasks() #url_for('populateIpInfo'))
	app.run(debug=False)
