#!/usr/bin/python3
#import subprocess

import re
import requests
import json
import configparser
import os
import argparse
import time


months = {'Jan': '01',
          'Feb': '02',
          'Mar': '03',
          'Apr': '04',
          'May': '05',
          'Jun': '06',
          'Jul': '07',
          'Aug': '08',
          'Sep': '09',
          'Oct': '10',
          'Nov': '11',
          'Dec': '12'}


def parselog(maillog):
    accounts = set()  # []
    maillog = open(maillog, 'r')
    for line in maillog:
        if (re.search("sshd.*Accepted", line)):
            # print(line)
            user, ip = re.findall(
                "for (\S*?) from ([\d\.\:a-zA-Z]*) port", line)[0]
            #print(user + " and ip "+ ip)
            atoms = line.split()
            month = atoms[0]
            day = atoms[1]
            # append({'user' : user, 'ip' : ip})
            accounts.add(""+ip+":!:"+user+":!:"+months[month]+":!:"+day)
    return accounts


def jsonify(accounts):
    res = []
    for account in accounts:
        newaccount = account.split(":!:")
        res.append({'ip': newaccount[0], 'user': newaccount[1],
                    'month': newaccount[2], 'day': newaccount[3], 'year': '2018'})
    return(json.dumps({'service': 'SSH', 'connections': res}))


def pushJSON(accounts, coreurl):
    #print('pushing ' + str(accounts) + ' to ' + coreurl)
    # print(accounts)
    # print(jsonify(accounts))
    for i in range(1, 10):
        try:
            r = requests.post(
                coreurl + "/api/addConnectionJSON", json=jsonify(accounts))
            break
        except:
            time.sleep(1)
            pass
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Uploads sshd logs')
    parser.add_argument('-c', type=str, help='config file')
    args = parser.parse_args()

    if args.c != None:
        configfiles = args.c
    else:
        configfiles = ["/etc/shsd.conf",
                       os.path.expanduser('~/.config/shsd.conf')]

    try:
        config = configparser.ConfigParser()
        config.read(configfiles)
        maillog = config['sshd']['authlog']
        coreurl = config['sshd']['coreurl']
    except:
        print('Cannot read config from ' + str(configfiles))
        exit(1)

    accounts = parselog(maillog)
    pushJSON(accounts, coreurl)
