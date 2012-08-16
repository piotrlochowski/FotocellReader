import serial
import binascii
import sys

#reload(sys)
#sys.setdefaultencoding('utf-8')

write = sys.stdout.write
write_err = sys.stderr.write


class Time():
	mm = 0
	ss = 0
	
class LapResult();
	numbre = ''
	lapTime = ''
	
	def isResultComplete():
		if number != null and  lapTime !=null
			return true
		else
			return false



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
				print int(x, 16)
				
			else :
				result.append(ord(x))
				print (ord(x))
			num-=1
		return result
	
	def getEventResult(byte):
		



try:
	sr = SerialReader()
	while 1:
		et = sr.getEventType()
		if et == 7
			#create Lap class
			sr.readStarNumber()
		if et == 0 and lap.startNumber != nulll
			#wait for lap result
			sr.readLapTime()
			#send result

		
	
	print sr.readBytes(4)
except serial.serialutil.SerialException:
        write_err ("Blad otwarcia portu\n")

