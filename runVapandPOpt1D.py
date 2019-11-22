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
numV=40#400
Vmin=16 #in Volts
Vmax=22#in Volts
Vscan = 0.05

DCBiasGuessMin = 0.5
valuesVap = [0]*5



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


try:
	SetChannel(Resource,DCBias_ChannelNumber)
	valuesDC = [0]*5
	VappliedDC=VoltageRamp(Vmin,Vmax,numV)
	t=np.arange(1,1+len(VappliedDC))
	VinDC=[]
	P=[]
	VaDC=[]
	print('Writing and reading applied/input voltage values, press Ctrl-C to quit...')
	line='  ID  |   Date/Time   |   DC Bias Voltage Applied (V)    |    Voltage Measured (V)    |    Power (nW)    '.format(*range(5))
	print(line)
	line='-' * 100
	print(line)
	#print(Vapplied[0])
	SetVoltage(Resource,DCBias_ChannelNumber,VappliedDC[0])
	time.sleep(5)
	for Vap in VappliedDC:
		valuesDC[0]=str(i)
		valuesDC[1]= str(datetime.now())
		valuesDC[2]="{0:.3f}".format(Vap)
		SetVoltage(Resource,DCBias_ChannelNumber,Vap)
		time.sleep(0.05) #Wait
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
		VinDC.append(vMeas)
		valuesDC[3]=str(vMeas)
		p=10**9*powermeter.read
		P.append(p)
		valuesDC[4]="{0:.3f}".format(p)
		line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} '.format(*valuesDC)
		print(line)
		query="INSERT INTO IM(datetime, DCVap, DCVin, P) values(NOW(), +"+valuesDC[2]+","+valuesDC[3]+","+valuesDC[4]+");"
		cur.execute(query)
		db.commit()
		i+=1
	VinDC = np.array(VinDC)
	P=np.array(P)
	Pmin = np.amin(P)
	Pmax = np.amax(P)
	eRatio=-10*np.log10(Pmin/Pmax)
	print("Exinction Ratio Lower Bound: ", eRatio)

	#Initial scan
	fig, axs = plt.subplots(1,1,num="1")
	PmW=[]
	for pnW in P:
		PmW.append(pnW*10**-6)
	PmW=np.array(PmW)
	axs.plot(VappliedDC,PmW, label = "Extinction Ratio = "+str(eRatio))
	axs.grid()
	axs.set_xlabel("Applied Voltage (V)")
	axs.set_ylabel(r"Power ($n W$)")
	figname="InitScan.png"
	plt.savefig(figname)


	PminIndex = np.where(P==Pmin)
	PminIndex=PminIndex[0]
	Va_minP=VappliedDC[PminIndex[0]]
	PmaxIndex = np.where(P==Pmax)
	PmaxIndex=PmaxIndex[0]
	Va_maxP=VappliedDC[PmaxIndex[0]]
	print("Va for min P: ",Va_minP)
	print("Pmin: ",Pmin)
	print("Va for max P: ",Va_maxP)
	print("Pmax: ",Pmax)
	SetVoltage(Resource,DCBias_ChannelNumber,Va_minP)
	time.sleep(10)
	print("Vin after setting Va for min P: ",float(Resource.query("MEAS:VOLT?").rstrip()))
	print("P (nW): ",10**9*powermeter.read)





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

	valuesVap = [0]*4
	Vapplied=VoltageStairs(1.275,1.245,12,60*60)
	#Vapplied = VoltageConst(1.245,3*3600)
	t=np.arange(1,1+len(Vapplied))
	fig=plt.figure()
	ax=plt.subplot(111)
	ax.plot(t/3600,Vapplied)
	ax.set_xlabel("Hours")
	ax.set_ylabel("Voltage (V)")
	plt.title("Applied Voltage vs. Time")
	fig.savefig("TotalScanTrace.png")
	plt.show()
	Vin=[]
	print('Writing and reading applied/input voltage values, press Ctrl-C to quit...')
	line='  ID  |   Date/Time   |    Voltage Applied (V)    |    Voltage Measured (V)    '.format(*range(4))
	print(line)
	line='-' * 75
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
		line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} '.format(*valuesVap)
		print(line)
		query="INSERT INTO VapVin(Vap, Vin, datetimeVap, datetimeVin) values("+valuesVap[2]+","+valuesVap[3]+", NOW(), NOW());"
		cur.execute(query)
		db.commit()

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
		print("Power: ", valuesDC[4])
		cur.execute(query)
		db.commit()

	#Feedback on power
		P=[]
		VinDC=[]
		SetChannel(Resource,DCBias_ChannelNumber)
		print(Va_minP)
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
		i+=1

	Vin = np.array(Vin)
	fig=plt.figure()
	ax=plt.subplot(111)
	ax.plot(t/3600,Vapplied, label = "Applied Voltage")
	ax.plot(t/3600,Vin, label = "Vin")
	ax.set_xlabel("Hours")
	ax.set_ylabel("Voltage (V)")
	ax.legend()
	plt.title("Voltage vs. Time")
	fig.savefig("PostScanTrace.png")
	plt.show()
except KeyboardInterrupt:
	print("")
	print("Quit")
	#DisableLVOutput(Resource)
db.close()
