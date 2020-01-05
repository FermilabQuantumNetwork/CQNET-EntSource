"""
This combines the code for controlling the setpoint temperature of the interferometer
and running the feedback on the DC Bias pin for Bob's intensity modulator, without
doing an initial scan for the feedback. You should try to optimize the IM manually first.

For each element of the voltage array for the thermistor setpoint, there is a
fine scan over the DC Bias for feedbacking on the power.

Bob has a ~50dB IM with two voltage pins (DC Bias and ER Tuning)


Requirements: Python3, VapScanFunc.py in same directory, packages listed below
and in VapScanFunc.py
OS: CentOS7

"""
from VapScanFunc import *
import pymysql
from ThorlabsPM100 import ThorlabsPM100, USBTMC



db = pymysql.connect(host="<IP ADDRESS>",  #Replace <IP ADDRESS> with the IP of computer with database. Local host if is same computer.
					 user="<USERNAME>", #Replace <USERNAME> with your username
					 passwd="<PASSWORD>",  #Replace <PASSWORD> with your password
					 database="teleportcommission",
					 charset='utf8mb4',
					 cursorclass=pymysql.cursors.DictCursor)

#Connect to powermeter
inst = USBTMC(device="/dev/usbtmc0")
powermeter = ThorlabsPM100(inst=inst)

#Changing Temp
Vap_ChannelNumber=1
numSteps=10
Vmin=0 #in Volts
Vmax=2 #in Volts


#DC Bias of IM
DCBias_ChannelNumber=2
Vmin=0 #in Volts
Vmax=22#in Volts
Vscan = 0.01

#Flag for Vap/temp scan run
finishedRun=False

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

valuesDC = [0]*5
valuesVap = [0]*4
values = []
try:
	SetChannel(Resource,DCBias_ChannelNumber) #Sets channel of powersupply
	Va_minP = float(Resource.query("MEAS:VOLT?").rstrip()) #Get current voltage setting
	print(Va_minP)
	print("Vin after setting to DCBiasGuessMin ",float(Resource.query("MEAS:VOLT?").rstrip()))
	print("P (nW): ",10**9*powermeter.read) #Measure from power meter
	starttime=datetime.now()
	curtime=starttime


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


	Vapplied=VoltageStairs(1.275,1.245,8,1)#5*60)
	#Vapplied = VoltageConst(1.245,3*3600)

	"""
	Plot what will be sent to power supply for temp run
	t=np.arange(1,1+len(Vapplied))
	fig=plt.figure()
	ax=plt.subplot(111)
	ax.plot(t/3600,Vapplied)
	ax.set_xlabel("Hours")
	ax.set_ylabel("Voltage (V)")
	plt.title("Applied Voltage vs. Time")
	"""

	Vin=[]
	print('Writing and reading applied/input voltage values, press Ctrl-C to quit...')
	# Print nice channel column headers.
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
		valuesVap[1]= str(time.ctime()) #Get current time
		valuesVap[2]="{0:.3f}".format(Vap)
		valuesVap[3]=SetVoltage(Resource,Vap_ChannelNumber,Vap) #Set voltage of power supply to Vap. Returns Vin, the voltage reported by power supply
		Vin.append(valuesVap[3])
		valuesVap[3]=str(valuesVap[3])
		#SQL command to insert data into database
		query="INSERT INTO VapVin(Vap, Vin, datetimeVap, datetimeVin) values("+valuesVap[2]+","+valuesVap[3]+", NOW(), NOW());"
		cur.execute(query)
		db.commit()

		#Prepare for Feedback: Insert current DC Bias voltage into database
		SetChannel(Resource,DCBias_ChannelNumber)
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
		valuesDC[0]=str(i)
		valuesDC[1]=str(datetime.now())
		valuesDC[2]="{0:.3f}".format(Va_minP)
		valuesDC[3] = str(vMeas)
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
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
		VappliedDC = VoltageRamp(vMeas-Vscan/2, vMeas+Vscan/2,40)
		SetVoltage(Resource,DCBias_ChannelNumber,VappliedDC[0])
		time.sleep(0.1)
		#Loops over each element in fine scan for DC Bias voltage
		for DCVap in VappliedDC:
			SetVoltage(Resource,DCBias_ChannelNumber,DCVap)
			vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
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
		PminIndex = np.where(P==Pmin) #Get index of min power from fine scan
		PminIndex=PminIndex[0]
		Va_minP=VappliedDC[PminIndex[0]] #Get voltage corresponding to min power from fine scan
		SetVoltage(Resource,DCBias_ChannelNumber,Va_minP) #Set to voltage of min power from previous scan
		i+=1
	Vin = np.array(Vin)
	finishedRun = True #Flagged that finished the temperature run
	while(True): #Sit on last value of temperature run until this script is terminated
		time.sleep(1) #Wait 1 second

		#Set and record voltage (thermistor set point)
		SetChannel(Resource,Vap_ChannelNumber)
		valuesVap[0]=str(i)
		valuesVap[1]= str(time.ctime())
		valuesVap[2]="{0:.3f}".format(Vapplied[-1])
		valuesVap[3]=SetVoltage(Resource,Vap_ChannelNumber,Vapplied[-1])
		Vin=np.append(Vin,valuesVap[3])
		valuesVap[3]=str(valuesVap[3])
		cur.execute(query)
		db.commit()

		#Record current DC Bias voltage and power
		SetChannel(Resource,DCBias_ChannelNumber)
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
		valuesDC[0]=str(i)
		valuesDC[1]=str(datetime.now())
		valuesDC[2]="{0:.3f}".format(Va_minP)
		valuesDC[3] = str(vMeas)
		p=10**9 * powermeter.read
		valuesDC[4]="{0:.3f}".format(p)

		query="INSERT INTO IM(datetime, DCVap, DCVin, P) values(NOW(), +"+valuesDC[2]+","+valuesDC[3]+","+valuesDC[4]+");"
		cur.execute(query)
		values = [valuesVap[0],valuesVap[1],valuesVap[2],valuesVap[3],valuesDC[2],valuesDC[3],valuesDC[4]]
		line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} | {5:>6} | {6:>6} '.format(*values)
		print(line)
		query="INSERT INTO VapVin(Vap, Vin, datetimeVap, datetimeVin) values("+valuesVap[2]+","+valuesVap[3]+", NOW(), NOW());"
		cur.execute(query)
		db.commit()

	#Feedback on power
		P=[]
		VinDC=[]
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
		VappliedDC = VoltageRamp(vMeas-Vscan/2, vMeas+Vscan/2,40)
		SetVoltage(Resource,DCBias_ChannelNumber,VappliedDC[0])
		time.sleep(0.1)
		for DCVap in VappliedDC:
			SetVoltage(Resource,DCBias_ChannelNumber,DCVap)
			vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
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
		i+=1


except KeyboardInterrupt:
	print("")
	print("Quit")
	Resource.write("SYSTEM:LOCAL")
	print("Set manual access")
	#if(finishedRun):
		#plt.show()

db.close()
