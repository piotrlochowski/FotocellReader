#!/usr/bin/env python
import serial
import binascii
import sys
import urllib2
import json

#reload(sys)
#sys.setdefaultencoding('utf-8')

write = sys.stdout.write
write_err = sys.stderr.write


class Time():
	mm = 0
	ss = 0
	
class SerialReader():
	ser = None

	def __init__ (self):
		self.ser = serial.Serial('/dev/ttyS0', 2400)	

	def readLapResult():
		return readInfo(4)

	def readBytes(self, num):
		result = [] 
		while num > 0:
			x = self.ser.read()
			if x.count('\\x') > 0 :
				replace(x, '\\X' '0x')
				result.append(int(x, 16))
				return int(x, 16)
				
			else :
				result.append(ord(x))
				return (ord(x))
			num-=1
		return result
	
	def getEventResult(byte):
		return ''

class RaceRecordSender():
	
	def sendLapTime(self, time):		
		data = '{"lap_nr": 1, "penalty": "11:08:26", "penalty_value": "22", "time": "11:08:25", "trial_result": "/py/api/v1/trial_result/1/"}'
		#data_json = json.dumps(data)
		host = "http://localhost/py/api/v1/lap/?format=json"
		req = urllib2.Request(host, data, {'content-type': 'application/json'})
		response_stream = urllib2.urlopen(req)
		response = response_stream.read()
		print(response)
	
	def postRequest():
		url = "http://localhost/py/api/v1/lap/?format=json"
		json_data = '{"lap_nr": 1, "penalty": "11:08:26", "penalty_value": "22", "resource_uri": "/api/v1/lap/2/", "time": "11:08:25", "trial_result": "/api/v1/trial_result/1/"}'
		
		opener = urllib2.build_opener()
		opener.addheaders = [('Accept', 'application/json'),
                                                ('Content-Type', 'application/json'),
                                                #('Authorization', 'Basic %s' % base64.encodestring('%s:%s' % (self.username, self.password))[:-1]), 
                                                ('User-Agent', 'Python-urllib/2.6')]

		req = urllib2.Request(url=url, data=json_data)
		#assert req.get_method() == 'POST'
		response = self.opener.open(req)
		print response.code

		return response
	
		
try:
	sr = SerialReader()
	rrs = RaceRecordSender()
	#while 1:
	#	print sr.readBytes(1)
	rrs.sendLapTime(0)
		#sr.postRequest
except serial.serialutil.SerialException:
        write_err ("Blad otwarcia portu\n")
