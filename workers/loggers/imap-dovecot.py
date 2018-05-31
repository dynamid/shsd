#!/usr/bin/python3

import subprocess
import re
import requests
import json

webappurl = "http://127.0.0.1:5000/"
dovecotlog = "../../logs/mail.log"

months = {'Jan' : '01',
        'Feb' : '02',
        'Mar' : '03',
        'Apr' : '04',
        'May' : '05',
        'Jun' : '06',
        'Jul' : '07',
        'Aug' : '08',
        'Sep' : '09',
        'Oct' : '10',
        'Nov' : '11',
        'Dec' : '12'}

def parselog():
    accounts = set()#[]
    maillog = open(dovecotlog,'r')
    for line in maillog:
        if (re.search("dovecot.*Login", line)):
            user = re.findall("user=<(.*?)>", line)[0]
            ip =  re.findall("rip=([\d\.]*)", line)[0]
            atoms = line.split()
            month = atoms[0]
            day = atoms[1]
            accounts.add(""+ip+"::"+user+"::"+months[month]+"::"+day) #append({'user' : user, 'ip' : ip})
    return accounts

def push(accounts):
    for account in accounts:
        #print(account)
        newaccount = account.split("::")
        #print(newaccount[0] + " and " + newaccount[1])
        r = requests.get(webappurl + "api/addConnection/IMAP/" + newaccount[0] + "/" + newaccount[1] + "/" + newaccount[2] + "/" + newaccount[3])
        #print(r.content)
    return

def jsonify(accounts):
    res = []
    for account in accounts:
        newaccount = account.split("::")
        res.append({'ip':newaccount[0], 'user': newaccount[1], 'month': newaccount[2], 'day': newaccount[3], 'year': '2018'})
    return(json.dumps({'service' : 'IMAP', 'connections' : res}))

def pushJSON(accounts):
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    r = requests.post(webappurl + "api/addConnectionJSON", json=jsonify(accounts))
    return


if __name__ == '__main__':
    accounts =  parselog()
    #print("Adding following connections : " + str(accounts))
    #print("\n\nIn JSON : " + jsonify(accounts))
    pushJSON(accounts)
