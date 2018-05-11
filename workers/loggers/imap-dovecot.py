#!/usr/bin/python3

import subprocess
import re
import requests

webappurl = "http://127.0.0.1:5000/"
dovecotlog = "../../logs/mail.log"

def parselog():
    accounts = set()#[]
    maillog = open(dovecotlog,'r')
    for line in maillog:
        if (re.search("dovecot.*Login", line)):
            user = re.findall("user=<(.*?)>", line)[0]
            ip =  re.findall("rip=([\d\.]*)", line)[0]
            accounts.add(""+ip+"::"+user) #append({'user' : user, 'ip' : ip})
    return accounts

def push(accounts):
    for account in accounts:
        #print(account)
        newaccount = account.split("::")
        #print(newaccount[0] + " and " + newaccount[1])
        r = requests.get(webappurl + "api/addConnection/IMAP/" + newaccount[0] + "/" + newaccount[1])
        #print(r.content)
    return

if __name__ == '__main__':
    accounts = parselog()
    print("Adding following connections : " + str(accounts))
    push(accounts)
