#!/usr/bin/python3

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
        if (re.search("dovecot.*Login", line)):
            user = re.findall("user=<(.*?)>", line)[0]
            # ip =  re.findall("rip=([\d\.]*)", line)[0]
            ip = re.findall("rip=([\d\.\:a-zA-Z]*)", line)[0]
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
    return(json.dumps({'service': 'IMAP', 'connections': res}))


def pushJSON(accounts, coreurl):
    # print('pushing ' + str(accounts) + ' to ' + coreurl)
    # print(accounts)
    # print(jsonify(accounts))
    for i in range(1, 10):
        try:
            requests.post(
                coreurl + "/api/addConnectionJSON", json=jsonify(accounts))
            break
        except:
            time.sleep(1)
            pass
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Uploads dovecot logs')
    parser.add_argument('-c', type=str, help='config file')
    args = parser.parse_args()

    if args.c is not None:
        configfiles = args.c
    else:
        configfiles = ["/etc/shsd.conf",
                       os.path.expanduser('~/.config/shsd.conf')]

    try:
        config = configparser.ConfigParser()
        config.read(configfiles)
        maillog = config['dovecot']['maillog']
        coreurl = config['dovecot']['coreurl']
    except:
        print('Cannot read config from ' + str(configfiles))
        exit(1)

    accounts = parselog(maillog)
    pushJSON(accounts, coreurl)
