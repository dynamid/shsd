#!/usr/bin/python3

import subprocess
import re
import requests

webappurl = "http://127.0.0.1:5000/"

def runarp():
    devices = []
    output = subprocess.run(["/usr/sbin/arp", "-n"], stdout=subprocess.PIPE)
    #print(output.stdout.decode('utf-8'))
    splitted = output.stdout.decode('utf-8').split('\n')
    for line in splitted:
        ip = re.findall("([\d]+\.[\d]+\.[\d]+\.[\d]+)", line)
        if len(ip) < 1:
            continue
        hw = re.findall("([\da-f]{2}\:[\da-f]{2}\:[\da-f]{2}\:[\da-f]{2}\:[\da-f]{2}\:[\da-f]{2})", line)
        if len(hw) < 1:
            continue
        #print("ligne " + str(ip) + " " + str(hw))
        devices.append({'ip' : ip[0], 'hw' : hw[0]})
    return devices

def push(devices):
    for device in devices:
        r = requests.get(webappurl + "api/addDevice/" + device['ip'] + "/" + device['hw'])
        #print(r.content)
    return

if __name__ == '__main__':
    devices = runarp()
    print("Adding following devices : " + str(devices))
    push(devices)

    testdevices =  [{'ip': '192.168.0.1', 'hw': 'f0:92:1c:5b:b5:da'},
            {'ip': '134.214.146.1', 'hw': 'ac:a0:16:0a:b6:00'},
            {'ip': '134.214.146.3', 'hw': 'a4:4e:31:07:21:58'}]
    print("Adding test devices : " + str(testdevices))
    push(testdevices)
