from VapScanFunc import *
import pymysql
from ThorlabsPM100 import ThorlabsPM100, USBTMC



db = pymysql.connect(host = "192.168.0.125", #Wired IPv4 Address
					user ="INQNET4", # this user only has access to CP
					password="Teleport1536!", # your password
					database="teleportcommission",
					charset='utf8mb4',
					#port = 5025,
					cursorclass=pymysql.cursors.DictCursor) #name of the data

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

finishedRun=False


VISAInstance=pyvisa.ResourceManager('@py')
Resource=InitiateResource()


cur = db.cursor()
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
	SetChannel(Resource,DCBias_ChannelNumber)
	Va_minP = float(Resource.query("MEAS:VOLT?").rstrip())
	print(Va_minP)
	print("Vin after setting to DCBiasGuessMin ",float(Resource.query("MEAS:VOLT?").rstrip()))
	print("P (nW): ",10**9*powermeter.read)
	starttime=datetime.now()
	curtime=starttime


#Start apply voltages
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
	t=np.arange(1,1+len(Vapplied))
	#fig=plt.figure()
	#ax=plt.subplot(111)
	#ax.plot(t/3600,Vapplied)
	#ax.set_xlabel("Hours")
	#ax.set_ylabel("Voltage (V)")
	#plt.title("Applied Voltage vs. Time")
	#fig.savefig("TotalScanTrace.png")
	#plt.show()
	Vin=[]
	print('Writing and reading applied/input voltage values, press Ctrl-C to quit...')
	line='  ID  |  Date/Time  |  VSetpoint (V)  |  Vin (V)  |  VSet DCBias (V)  |  Vin DCBias (V)  |  P (nW)  '.format(*range(7))
	print(line)
	line='-' * 100
	print(line)
	for Vap in Vapplied:
		time.sleep(1) #Wait 1 second
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
	Vin = np.array(Vin)
	#fig=plt.figure()
	#ax=plt.subplot(111)
	#ax.plot(t/3600,Vapplied, label = "Applied Voltage")
	#ax.plot(t/3600,Vin, label = "Vin")
	#ax.set_xlabel("Hours")
	#ax.set_ylabel("Voltage (V)")
	#ax.legend()
	#plt.title("Voltage vs. Time")
	#fig.savefig("PostScanTrace.png")
	finishedRun = True
	while(True):
		time.sleep(1) #Wait 1 second
		SetChannel(Resource,Vap_ChannelNumber)
		valuesVap[0]=str(i)
		valuesVap[1]= str(time.ctime())
		valuesVap[2]="{0:.3f}".format(Vapplied[-1])
		valuesVap[3]=SetVoltage(Resource,Vap_ChannelNumber,Vapplied[-1])
		Vin=np.append(Vin,valuesVap[3])
		valuesVap[3]=str(valuesVap[3])
		cur.execute(query)
		db.commit()

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
