#!/usr/bin/python3

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
        atoms = line.split()
        # print(atoms)
        user = atoms[2]
        if (user == '-'):
            continue
        ip = atoms[0]
        date = atoms[3].split(':')
        month = date[0].split('/')[1]
        day = date[0].split('/')[0][1:]
        year = date[0].split('/')[2]
        # append({'user' : user, 'ip' : ip})
        accounts.add(""+ip+":!:"+user+":!:"+months[month]+":!:"+day+":!:"+year)
    # print(accounts)
    return accounts


def jsonify(accounts):
    res = []
    for account in accounts:
        newaccount = account.split(":!:")
        res.append({'ip': newaccount[0], 'user': newaccount[1],
                    'month': newaccount[2], 'day': newaccount[3], 'year': newaccount[4]})
    return(json.dumps({'service': 'HTTP', 'connections': res}))


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
    parser = argparse.ArgumentParser(description='Uploads nginx logs')
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
        authlog = config['nginx']['authlog']
        coreurl = config['nginx']['coreurl']
    except:
        print('Cannot read config from ' + str(configfiles))
        exit(1)

    for f in os.listdir(authlog):
        if f.endswith("access.log"):
            accounts = parselog(authlog + "/" + f)
            pushJSON(accounts, coreurl)
