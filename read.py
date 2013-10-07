#!/usr/bin/env python
import base64
import serial
import binascii
import sys
import urllib2
import json

write = sys.stdout.write
write_err = sys.stderr.write


class Time():
    mm = 0
    ss = 0


class SerialReader():
    ser = None

    def __init__(self):
        self.ser = serial.Serial('/dev/ttyS0', 2400)

    def readLapResult():
        return readInfo(4)

    def readBytes(self, num):
        result = []
        while num > 0:
            x = self.ser.read()
            if x.count('\\x') > 0:
                replace(x, '\\X' '0x')
                result.append(int(x, 16))
                return int(x, 16)

            else:
                result.append(ord(x))
                return (ord(x))
            num -= 1
        return result

    def getEventResult(byte):
        return ''


class RaceRecordSender():
    def sendLapTime(self, time):
        url = "http://localhost:8000/py/api/v1/lap/?format=json"
        data = {"lap_nr": 1, "penalty": "11:08:26", "penalty_value": "22", "time": time, "trial_result": "/py/api/v1/trial_result/1/"}

        auth = 'Basic %s' % base64.encodestring('%s:%s' % ('piziem', 'pass4pizi'))[:-1]

        req = urllib2.Request(url, json.dumps(data), {'content-type': 'application/json', 'Authorization': auth})
        response_stream = urllib2.urlopen(req)
        response = response_stream.read()

    def postRequest(self, time):
        url = "http://localhost:8000/py/api/v1/lap/?format=json"
        data = {"lap_nr": 1, "penalty": "11:08:26", "penalty_value": "22", "time": time, "trial_result": "/py/api/v1/trial_result/1/"}

        opener = urllib2.build_opener()
        auth = 'Basic %s' % base64.encodestring('%s:%s' % ('piziem', 'pass4pizi'))[:-1]
        opener.addheaders = [('Accept', 'application/json'),
                             ('Content-Type', 'application/json'),
                             #('Authorization', auth),
                             ('User-Agent', 'Python-urllib/2.6')]

        req = urllib2.Request(url=url, data=json.dumps(data))
        assert req.get_method() == 'POST'
        response = opener.open(req)

        return response


try:
    sr = SerialReader()
    rrs = RaceRecordSender()
    #while 1:
        #print sr.readBytes(1)
    rrs.sendLapTime("11:08:25")
    #rrs.postRequest("11:08:25")

except serial.serialutil.SerialException:
    write_err("Blad otwarcia portu\n")
