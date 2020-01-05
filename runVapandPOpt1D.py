"""
This combines the code for controlling the setpoint temperature of the interferometer
and running the feedback on the DC Bias pin for Bob's intensity modulator, with an
initial scan for the feedback.

For each element of the voltage array for the thermistor setpoint, there is a
fine scan over the DC Bias for feedbacking on the power.

Bob has a ~50dB IM with two voltage pins (DC Bias and ER Tuning)


Requirements: Python3, VapScanFunc.py in same directory, packages listed below
and in VapScanFunc.py
OS: CentOS7

"""

from VapScanFunc import *
import pymysql
import pyvisa as visa
import socket
import time
import math
from ThorlabsPM100 import ThorlabsPM100, USBTMC
import matplotlib.pyplot as plt
import matplotlib as mpl



db = pymysql.connect(host="<IP ADDRESS>",  #Replace <IP ADDRESS> with the IP of computer with database. Local host if is same computer.
					 user="<USERNAME>", #Replace <USERNAME> with your username
					 passwd="<PASSWORD>",  #Replace <PASSWORD> with your password
					 database="teleportcommission",
					 charset='utf8mb4',
					 cursorclass=pymysql.cursors.DictCursor) #name of the data

#Command to set directory for saving figures produced by this script
mpl.rcParams["savefig.directory"] = os.chdir(os.path.dirname("/home/inqnet4/Desktop/CQNET/EntSource"))


#Connect to powermeter
VISAInstance=pyvisa.ResourceManager('@py')
resourceName='USB0::4883::32888::P0023460::0::INSTR'
inst=VISAInstance.open_resource(resourceName)
print(inst.ask("*IDN?"))
powermeter = ThorlabsPM100(inst=inst)


#Create array to be sent to powersupply for temp scan
maxV = 1.2725
minV=1.255
stepSize = 0.001
numSteps = (maxV - minV)/stepSize
numSteps=int(round(numSteps))
stepTime = 60*60 #Seconds
print("numSteps = ", numSteps)
print("maxV = ", maxV)
print("minV = ", minV)
print("stepTime (min)= ", stepTime/60)
print("totalTime (min) = ", numSteps * stepTime/60)
VSetArr=VoltageConst(maxV,120*60)
VSetArr = np.append(VSetArr,VoltageStairs(maxV,minV,numSteps,stepTime))
#VSetArr=VoltageStairs(maxV,minV,numSteps,stepTime)


#Thermistor params
R0=10000
T0 = 25+273.15
beta = 3435
rInf = R0*math.exp(-beta/T0)
V0 = 2.5


#Changing Temp
Vap_ChannelNumber=1
numSteps=10
Vmin=0 #in Volts
Vmax=2 #in Volts


#DC Bias of IM
DCBias_ChannelNumber=2
numV=400
Vmin=0 #in Volts
Vmax=22#in Volts
Vscan = 0.1

DCBiasGuessMin = 0.5
valuesVap = [0]*5


#Convert voltage setpoint array to thermistor temp
TSetArr=[]
for i in range(len(VSetArr)):
	Rt_Vap = VSetArr[i]*R0/(V0-VSetArr[i])
	t = beta/(math.log(Rt_Vap/rInf))
	TSetArr.append(t)
print(TSetArr[0]-273.15)
print(TSetArr[-1]-273.15)


#Connect to powersupply
VISAInstance=pyvisa.ResourceManager('@py')
Resource=InitiateResource()


#Create cursor to select data from mysql.
cur = db.cursor()

#Get max id for printing out data in terminal
query = "SELECT max(id) from IM"
cur.execute(query)
result = cur.fetchall()
resultDict = result[0]
maxid=resultDict["max(id)"]
if maxid is None:
	maxid=0
i = maxid +1


try:
	SetChannel(Resource,DCBias_ChannelNumber) #Sets channel of powersupply
	valuesDC = [0]*5
	VappliedDC=VoltageRamp(Vmin,Vmax,numV) #Array for initial scan of DC Bias
	t=np.arange(1,1+len(VappliedDC)) #for plotting
	VinDC=[]
	P=[]
	VaDC=[]
	print('Writing and reading applied/input voltage values, press Ctrl-C to quit...')
	line='  ID  |   Date/Time   |   DC Bias Voltage Applied (V)    |    Voltage Measured (V)    |    Power (nW)    '.format(*range(5))
	print(line)
	line='-' * 99
	print(line)
	SetVoltage(Resource,DCBias_ChannelNumber,VappliedDC[0]) #Set to first element of initial scan to settle before start
	time.sleep(5)
	for Vap in VappliedDC: #Loops through elements of DC Bias initial scan, sets power supply to each element.
		valuesDC[0]=str(i)
		valuesDC[1]= str(datetime.now())
		valuesDC[2]="{0:.3f}".format(Vap)
		SetVoltage(Resource,DCBias_ChannelNumber,Vap) #Set DC Bias channel to Vap
		time.sleep(0.05) #Wait
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip()) #DC Bias voltage reported by power supply
		VinDC.append(vMeas)
		valuesDC[3]=str(vMeas)
		p=10**9*powermeter.read #current optical power
		P.append(p)
		valuesDC[4]="{0:.3f}".format(p)
		line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} '.format(*valuesDC)
		print(line)
		#SQL command to insert data into database
		query="INSERT INTO IM(datetime, DCVap, DCVin, P) values(NOW(), +"+valuesDC[2]+","+valuesDC[3]+","+valuesDC[4]+");"
		cur.execute(query)
		db.commit()
		i+=1
	VinDC = np.array(VinDC)
	P=np.array(P)
	Pmin = np.amin(P)
	Pmax = np.amax(P)
	eRatio=-10*np.log10(Pmin/Pmax)
	print("Exinction Ratio Lower Bound: ", eRatio) #Max extinction ratio from initial scan

	#Initial scan plot
	fig, axs = plt.subplots(1,1,num="1")
	PmW=[]
	for pnW in P:
		PmW.append(pnW*10**-6)
	PmW=np.array(PmW)
	axs.plot(VappliedDC,PmW, label = "Extinction Ratio = "+str(eRatio))
	axs.grid()
	axs.set_xlabel("Applied Voltage (V)")
	axs.set_ylabel(r"Power ($n W$)")


	#Get index corresponding to min of power from init scan
	PminIndex = np.where(P==Pmin)
	PminIndex=PminIndex[0]
	Va_minP=VappliedDC[PminIndex[0]] #Find DC Bias  voltage value corresponding to min power

	#Get index corresponding to max of power from init scan
	PmaxIndex = np.where(P==Pmax)
	PmaxIndex=PmaxIndex[0]
	Va_maxP=VappliedDC[PmaxIndex[0]]  #Find DC Bias voltage value corresponding to max power


	print("Va for min P: ",Va_minP)
	print("Pmin: ",Pmin)
	print("Va for max P: ",Va_maxP)
	print("Pmax: ",Pmax)

	#Set powersupply voltage to min power
	SetVoltage(Resource,DCBias_ChannelNumber,Va_minP)
	time.sleep(10) #Wait to settle at the optimal voltage
	print("Vin after setting Va for min P: ",float(Resource.query("MEAS:VOLT?").rstrip()))
	print("P (nW): ",10**9*powermeter.read)




#Start applying voltages for temp scan
	SetChannel(Resource,Vap_ChannelNumber)
	cur = db.cursor()
	query = "SELECT max(id) from VapVin"
	cur.execute(query)
	result = cur.fetchall()
	resultDict = result[0]
	maxid=resultDict["max(id)"]
	if maxid is None:
		maxid=0
	i = maxid +1

	valuesVap = [0]*4
	Vapplied=VSetArr
	t=np.arange(1,1+len(Vapplied)) #For plotting
	"""
	Plot what going to send to powersupply
	fig=plt.figure()
	ax=plt.subplot(111)
	ax.plot(4*t/3600,Vapplied)
	ax.set_xlabel("Hours")
	ax.set_ylabel("Voltage (V)")
	plt.title("Applied Voltage vs. Time")
	fig.savefig("TotalScanTraceNov27.png")
	plt.show()
	"""
	Vin=[]
	print('Writing and reading applied/input voltage values, press Ctrl-C to quit...')
	line='  ID  |  Date/Time  |  VSetpoint (V)  |  Vin (V)  |  VSet DCBias (V)  |  Vin DCBias (V)  |  P (nW)  '.format(*range(7))
	print(line)
	line='-' * 100
	print(line)

	#Temp scan: Loops through elements in Vapplied array, sets power supply to each element
	#For each temp, do feedback on IM
	for Vap in Vapplied:
		time.sleep(1) #Wait 1 second
		SetChannel(Resource,Vap_ChannelNumber)
		valuesVap[0]=str(i)
		valuesVap[1]= str(time.ctime())
		valuesVap[2]="{0:.3f}".format(Vap)
		valuesVap[3]=SetVoltage(Resource,Vap_ChannelNumber,Vap) #Set voltage of power supply to Vap. Returns Vin, the voltage reported by power supply
		Vin.append(valuesVap[3])
		valuesVap[3]=str(valuesVap[3])
		query="INSERT INTO VapVin(Vap, Vin, datetimeVap, datetimeVin) values("+valuesVap[2]+","+valuesVap[3]+", NOW(), NOW());"
		cur.execute(query)
		db.commit()

		#Prepare for Feedback: Insert current DC Bias voltage into database
		SetChannel(Resource,DCBias_ChannelNumber)
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
		valuesDC[0]=str(i)
		valuesDC[1]=str(datetime.now())
		valuesDC[2]="{0:.3f}".format(Va_minP)
		vmeas = SetVoltage(Resource, DCBias_ChannelNumber,Va_minP)
		valuesDC[3]="{0:.3f}".format(vmeas)
		p=10**9 * powermeter.read
		valuesDC[4]="{0:.3f}".format(p)
		#SQL command to insert data into database
		query="INSERT INTO IM(datetime, DCVap, DCVin, P) values(NOW(), +"+valuesDC[2]+","+valuesDC[3]+","+valuesDC[4]+");"
		values = [valuesVap[0],valuesVap[1],valuesVap[2],valuesVap[3],valuesDC[2],valuesDC[3],valuesDC[4]]
		line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} | {5:>6} | {6:>6} '.format(*values)
		print(line)
		cur.execute(query)
		db.commit()

		#Feedback on power
		P=[]
		VinDC=[]
		SetChannel(Resource,DCBias_ChannelNumber)
		vMeas = SetVoltage(Resource, DCBias_ChannelNumber,Va_minP)
		VappliedDC = VoltageRamp(vMeas-Vscan/2, vMeas+Vscan/2,40)
		SetVoltage(Resource,DCBias_ChannelNumber,VappliedDC[0])
		time.sleep(0.1)
		#Loops over each element in fine scan for DC Bias voltage
		for DCVap in VappliedDC:
			vMeas=SetVoltage(Resource,DCBias_ChannelNumber,DCVap)
			VinDC.append(vMeas)
			p=0
			#Gets average of 10 powermeter measurements in rapid succession
			for s in range(10):
				p=10**9*powermeter.read
				p=p+p
			p=p/10
			P.append(p)
		P=np.array(P)
		VinDC=np.array(VinDC)
		Pmin = np.amin(P) #Get min power from fine scan
		PminIndex = np.where(P==Pmin)  #Get index of min power from fine scan
		PminIndex=PminIndex[0]
		Va_minP=VappliedDC[PminIndex[0]] #Get voltage corresponding to min power from fine scan
		SetVoltage(Resource,DCBias_ChannelNumber,Va_minP) #Set to voltage of min power from previous scan
		i+=1
	Vap=Vapplied[-1]
	while True:  #Sit on last value of temperature run until this script is terminated
		time.sleep(1) #Wait 1 second

		#Set and record voltage (thermistor set point)
		SetChannel(Resource,Vap_ChannelNumber)
		valuesVap[0]=str(i)
		valuesVap[1]= str(time.ctime())
		valuesVap[2]="{0:.3f}".format(Vap)
		valuesVap[3]=SetVoltage(Resource,Vap_ChannelNumber,Vap)
		Vin.append(valuesVap[3])
		valuesVap[3]=str(valuesVap[3])
		query="INSERT INTO VapVin(Vap, Vin, datetimeVap, datetimeVin) values("+valuesVap[2]+","+valuesVap[3]+", NOW(), NOW());"
		cur.execute(query)
		db.commit()

		#Record current DC Bias voltage and power
		SetChannel(Resource,DCBias_ChannelNumber)
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
		valuesDC[0]=str(i)
		valuesDC[1]=str(datetime.now())
		valuesDC[2]="{0:.3f}".format(Va_minP)
		vmeas = SetVoltage(Resource, DCBias_ChannelNumber,Va_minP)
		valuesDC[3]="{0:.3f}".format(vmeas)
		p=10**9 * powermeter.read
		valuesDC[4]="{0:.3f}".format(p)

		query="INSERT INTO IM(datetime, DCVap, DCVin, P) values(NOW(), +"+valuesDC[2]+","+valuesDC[3]+","+valuesDC[4]+");"
		values = [valuesVap[0],valuesVap[1],valuesVap[2],valuesVap[3],valuesDC[2],valuesDC[3],valuesDC[4]]
		line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} | {5:>6} | {6:>6} '.format(*values)
		print(line)
		cur.execute(query)
		db.commit()

	#Feedback on power
		P=[]
		VinDC=[]
		SetChannel(Resource,DCBias_ChannelNumber)
		vMeas = SetVoltage(Resource, DCBias_ChannelNumber,Va_minP)
		VappliedDC = VoltageRamp(vMeas-Vscan/2, vMeas+Vscan/2,40)
		SetVoltage(Resource,DCBias_ChannelNumber,VappliedDC[0])
		time.sleep(0.1)
		for DCVap in VappliedDC:
			vMeas=SetVoltage(Resource,DCBias_ChannelNumber,DCVap)
			VinDC.append(vMeas)
			p=0
			for s in range(10):
				p=10**9*powermeter.read
				p=p+p
			p=p/10
			P.append(p)
		P=np.array(P)
		VinDC=np.array(VinDC)
		Pmin = np.amin(P)
		PminIndex = np.where(P==Pmin)
		PminIndex=PminIndex[0]
		Va_minP=VappliedDC[PminIndex[0]]
		SetVoltage(Resource,DCBias_ChannelNumber,Va_minP)


	Vin = np.array(Vin)
	fig=plt.figure()
	"""
	Plot the run
	ax=plt.subplot(111)
	ax.plot(4*t/3600,Vapplied, label = "Applied Voltage")
	ax.plot(4*t/3600,Vin, label = "Vin")
	ax.set_xlabel("Hours")
	ax.set_ylabel("Voltage (V)")
	ax.legend()
	plt.title("Voltage vs. Time")
	fig.savefig("PostScanTraceNov27.png")
	plt.show()
	"""
except KeyboardInterrupt:
	print("")
	print("Quit")
	#DisableLVOutput(Resource)
db.close()
