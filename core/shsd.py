#!/usr/bin/python3

from flask import *
from sqlalchemy import *
from sqlalchemy.sql import *
from sqlalchemy.orm import scoped_session, sessionmaker
#from manuf import manuf
import datetime
import re
import requests
import time
import geojson
import json
import collections
import threading
import configparser, argparse, os
import GeoIP
import string


# local imports
from daemon import startBackgoundTasks, updateIPInfo, isLocalIP
from database import *

#p = manuf.MacParser(update=False)
app = Flask(__name__)
configfiles = ["/etc/shsd.conf", os.path.expanduser('~/.config/shsd.conf')]

def getCurrentUser():
	user = request.args.get("user", "user5")
	return user

@app.route('/')
@app.route('/index')
def index():
	return render_template('index.html', center_map=getAvgPositions(getCurrentUser()), geojson=url_for('getGeoJSON', user=getCurrentUser()),
	colors_to_print=getColorsFromDB(getCurrentUser()))

@app.route('/details')
def details():
	return render_template('details.html', devices=getDevices(), connections=getConnections())

@app.route('/about')
def about():
	return render_template('about.html')

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
								'ip_as' : row[accounts.c.ip_as],
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
			if (geoloc == 'onyphe'):
				Session.execute(accounts.insert(), [
		                	{'login': user, 'ip': ip, 'firstseen': date, 'lastseen': date, 'is_populated': False}
		           ])
			elif (geoloc == 'geoip'):
				# print('adding ' + ip)
				if (isLocalIP(ip)):
					new_as = "LAN"
					new_org = "LAN"
					new_geoloc = geoip_loc.record_by_addr(myip)
				else:
					tmp = geoip_as.org_by_addr(ip).split()
					new_as = tmp[0]
					new_org = " ".join(tmp[1:])
					new_geoloc = geoip_loc.record_by_addr(ip)
				if (new_as != None and new_geoloc != None):
					# print ("" + str(new_as) + str(new_geoloc))
					Session.execute(accounts.insert(), [
							{'login': user, 'ip': ip, 'firstseen': date, 'lastseen': date, 'is_populated': True,
							 'ip_org' : new_org, 'ip_country':new_geoloc['country_name'],
							 'ip_countrycode':new_geoloc['country_code'], 'ip_city':new_geoloc['city'],
							 'ip_longitude':new_geoloc['longitude'], 'ip_latitude':new_geoloc['latitude'],
							 'ip_as':new_as}
   						])
				else:   # failed to find an entry in the local geoip, failing back to onyphe
					print("no geoip entry for " + ip + ", failing back to onyphe")
					Session.execute(accounts.insert(), [
				               	{'login': user, 'ip': ip, 'firstseen': date, 'lastseen': date, 'is_populated': False}
				         ])
			else:
				print('no geoloc')
				Session.execute(accounts.insert(), [
		                	{'login': user, 'ip': ip, 'firstseen': date, 'lastseen': date, 'is_populated': True}
		           ])
		else:
			s = select([accounts.c.login, accounts.c.ip, accounts.c.lastseen]).where(and_(
					accounts.c.ip == ip, accounts.c.login == user))
			for row in Session.execute(s):
				olddate = row[accounts.c.lastseen]
				if (date > olddate):
					Session.execute(accounts.update().where(and_(accounts.c.ip == ip, accounts.c.login == user)).values(lastseen=date))
	try:
		Session.commit()
	except:
		Session.rollback()
	Session.remove()
	#threading.Thread(target=updateIPInfo).start()
	#startBackgoundTasks()
	return("JSON ok")
#-----------------------GET PORT FROM SHSD.CONF
def getPort():
	myfile = open("/etc/shsd.conf", "r")
	data = str(myfile.read())
	data = data.split("127.0.0.1:",1)[1]
	data = data.split('\n', 1)[0]
	return data
getPort()
#-----------------------MARKERS COLORS
as_colorlist = ["#FE0000","#FD0065","#00FAD0","#5C00FA","#002AFA","#00A7FA","#00FA00","#FAE900","#FA7500","#D300FD"]
def colorAs(user):
	c = select([ascolors.c.id_color]).where(ascolors.c.uid == user).distinct().count()
	nb_colors = Session.execute(c).scalar()
	return nb_colors

def getASColor(asn, user):  # return the color and creates it if needed

	nb_c = select([ascolors.c.id_color]).where(and_(
	ascolors.c.uid == user,ascolors.c.ip_as == asn)).count()
	nb_color = Session.execute(nb_c).scalar()#Si le couple as/user existe, on récupère la couleur

	if nb_color != 0:
		c = select([ascolors.c.id_color]).where(and_(ascolors.c.uid == user , ascolors.c.ip_as == asn))
		for rows in Session.execute(c):#il n'y a qu'un seul résultat (normalement)
			id = rows[ascolors.c.id_color]
			as_color = as_colorlist[id]
			#Session.execute(c).first()

	else:#s'il n'existe pas, alors on crée une ligne dans la table ascolors
		id = colorAs(user)
		if id > 10 : # le cas où toutes les couleurs de la table son utilisées
			as_color = "000000"
		else:
			as_color = as_colorlist[id]
		Session.execute(ascolors.insert(), [
					{'id_color': id, 'uid': user, 'ip_as': asn} #, 'color': as_color}
		   ])
	return as_color

def getColorsFromDB(user):
	c = select([ascolors.c.id_color, ascolors.c.ip_as]).where(ascolors.c.uid == user)
	col = []
	for row in Session.execute(c):
		s = select([accounts.c.ip_org]).where(and_(accounts.c.login == user,accounts.c.ip_as == row[ascolors.c.ip_as])).distinct()
		for i in Session.execute(s):
			color = {"asn":"color"}
			color['asn'] = i[accounts.c.ip_org]
			color['color'] = as_colorlist[row[ascolors.c.id_color]]
			col.append(color)
	legend = {'legend' : col}
	json_data = json.dumps(legend)
	return json_data
#-----------------------MARKERS SIZE
def markerSize(first,last):
	delta = last - first
	size = "small"
	if delta.days < 6 and last.month == first.month : #s'il y a moins de 5 jours d'écart entre la première et la dernière connexion
		size = "large"
	elif delta.days > 5 and delta.days < 10 and last.month == first.month:
		size = "medium"
	else:
		size = "small"
	return size


#ajouter dynamiquement les markers sur la map
@app.route('/api/getGeoJSON/<user>')
def getGeoJSON(user):
	my_feature = []

	s = select([accounts.c.ip_longitude,accounts.c.ip_latitude,accounts.c.ip_city,accounts.c.ip,
	accounts.c.ip_org, accounts.c.ip_as,accounts.c.login, accounts.c.firstseen, accounts.c.lastseen]).where(accounts.c.login == user).distinct()

	for row in Session.execute(s):
		as_color = getASColor(row[accounts.c.ip_as],row[accounts.c.login])
		size = markerSize(row[accounts.c.firstseen],row[accounts.c.lastseen])

		if row[accounts.c.ip_latitude] != None and row[accounts.c.ip_longitude] != None:
			if row[accounts.c.ip_city] == 'LAN':
				my_feature.append(geojson.Feature(geometry=geojson.Point((row[accounts.c.ip_longitude], row[accounts.c.ip_latitude])),
				properties={
		"marker-color": as_color,
		"marker-size": size,
		"marker-symbol": "home",
		"description": "ip : " + row[accounts.c.ip] + " | Org : " + row[accounts.c.ip_org] + " | Firstseen : "+str(row[accounts.c.firstseen]) + " | Lastseen : " + str(row[accounts.c.lastseen])
		}))
			else :
				my_feature.append(geojson.Feature(geometry=geojson.Point((row[accounts.c.ip_longitude], row[accounts.c.ip_latitude])),
				properties={
		"marker-color": as_color,
		"marker-size": size,
		"marker-symbol": "telephone",
		"description": "ip : " + row[accounts.c.ip] + " | Org : " + row[accounts.c.ip_org]+ " | Firstseen : "+str(row[accounts.c.firstseen]) + " | Lastseen : " + str(row[accounts.c.lastseen])
		}))

	Session.commit()
	Session.close()
	mygeojson = geojson.FeatureCollection(my_feature)
	return (geojson.dumps(mygeojson, sort_keys=True))

#moyenne des latitude et longitude
def getAvgPositions(user):
	pos = []
	delta_lat = []
	delta_long = []
#point central
	min = select([func.min(accounts.c.ip_latitude),func.min(accounts.c.ip_longitude)]).where(accounts.c.login == user).distinct()
	for row in Session.execute(min):
		pos.append(row[0])
		pos.append(row[1])

	max = select([func.max(accounts.c.ip_latitude),func.max(accounts.c.ip_longitude)]).where(accounts.c.login == user).distinct()
	for row in Session.execute(max):
		pos.append(row[0])
		pos.append(row[1])

	return pos
#liste des couleurs


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='SHSD Core')
	parser.add_argument('-c', type=str, help='config file')
	args = parser.parse_args()

	if args.c != None:
		configfiles = args.c

try:
	config = configparser.ConfigParser()
	config.read(configfiles)
	databasef = config['core']['database']
	geoloc = config['core']['geoloc']
	if (geoloc == 'geoip'):
		geoipdb = config['core']['geoipdb']
		try:
			geoip_loc = GeoIP.open(geoipdb + "/GeoIPCity.dat", GeoIP.GEOIP_STANDARD)
			geoip_as = GeoIP.open(geoipdb + "/GeoIPASNum.dat", GeoIP.GEOIP_STANDARD)
		except:
			print('Cannot open GeoIP database. Did you install it ? (apt-get install geoip-database-contrib)')
			exit(1)
except:
	print('Cannot read config from ' + str(configfiles))
	exit(1)

engine = create_engine(databasef, echo=False)
metadata.create_all(engine)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

myip = requests.get('https://api.ipify.org').text
print('my ip is ' + myip)

startBackgoundTasks(Session) #url_for('populateIpInfo'))

if __name__ == '__main__':
	app.run(debug=False,port=getPort())
