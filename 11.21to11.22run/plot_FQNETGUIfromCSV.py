#!/usr/bin/python2.7

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl
#import tkinter
#matplotlib.use('TkAgg')
import datetime
import math
import pymysql
import os
import time

figname = "plot_FQNETGUINov21to22png"

#START_TIME = '2019-11-19 16:31:00'
START_TIME = '2019-11-21 18:13:30'
END_TIME = '2019-11-22 07:00:00'#'NOW()'

mpl.rcParams["savefig.directory"] = os.chdir(os.path.dirname("/home/inqnet1/Desktop/CQNET/CQNET-Interf"))


#Thermistor params
R0=10000
T0 = 25+273.15
beta = 3435
rInf = R0*math.exp(-beta/T0)
V0 = 2.5


#connect to database


T1 = []
time_T1 = []
P = []
time_P = []
Vap = []
time_Vap = []
Vin=[]
time_Vin = []
and1=[]
and2 = []
and3 = []
abstime=[]

T_Vap = []
T_Vin = []
try:
	db = pymysql.connect(host="192.168.0.125",  # this PC
						 user="inqnet1",
						 passwd="Teleport1536!",  # your password
						 db="teleportcommission",
						 charset='utf8mb4',
						 cursorclass=pymysql.cursors.DictCursor)
	with db.cursor() as cur:

		TABLE_NAME = "VapVin"
		queryVapVin = "SELECT Vap, Vin,datetimeVap,datetimeVin FROM "+TABLE_NAME+" WHERE datetimeVap BETWEEN {ts %s} AND {ts %s}"
		TABLE_NAME = "Temp"
		queryT1 = "SELECT T1, datetimeT1 FROM "+TABLE_NAME+" WHERE datetimeT1 BETWEEN {ts %s} AND {ts %s}"
		TABLE_NAME = "IM"
		queryP = "SELECT P, datetime FROM "+TABLE_NAME+" WHERE datetime BETWEEN {ts %s} AND {ts %s}"
		TABLE_NAME = "FQNETGUI"
		startid=19218
		startime = 132
		queryFQNETGUI = "SELECT and1, and2, and3, abstime FROM "+TABLE_NAME+" WHERE id > "+str(startid)+" and abstime > "+str(startime)


		cur.execute(queryT1, (START_TIME,END_TIME,))
		row = cur.fetchone()
		while row is not None:
			T1.append(row["T1"])
			time_T1.append(row["datetimeT1"])
			row = cur.fetchone()

		cur.execute(queryP, (START_TIME,END_TIME,))
		row = cur.fetchone()
		while row is not None:
			P.append(10**6 * row["P"])
			time_P.append(row["datetime"])
			row = cur.fetchone()

		cur.execute(queryVapVin, (START_TIME,END_TIME,))
		row = cur.fetchone()
		while row is not None:
			Vap.append(row["Vap"])
			time_Vap.append(row["datetimeVap"])
			Vin.append(row["Vin"])
			time_Vin.append(row["datetimeVin"])
			row = cur.fetchone()

		cur.execute(queryFQNETGUI)
		row = cur.fetchone()
		while row is not None:
			and1.append(row["and1"])
			and2.append(row["and2"])
			and3.append(row["and3"])
			abstime.append(row["abstime"])
			row = cur.fetchone()



		time_T1_first = str(time_T1[0])
		print("time_T1_first=",time_T1_first )
		time_T1_last = str(time_T1[-1])
		first_time_T1 = datetime.datetime.strptime(time_T1_first,'%Y-%m-%d %H:%M:%S')
		time_T1_dt=[]
		time_T1_el_mins=[]

		time_P_first = str(time_P[0])
		print("time_P_first=",time_P_first )
		time_P_last = str(time_P[-1])
		first_time_P = datetime.datetime.strptime(time_P_first,'%Y-%m-%d %H:%M:%S')
		time_P_dt=[]
		time_P_el_mins=[]


		time_Vap_first = str(time_Vap[0])
		print("time_Vap_first=",time_Vap_first )
		time_Vap_last = str(time_Vap[-1])
		# if n==1:
		# 	print("time_Vap_last=",time_Vap_last )
		first_time_Vap = datetime.datetime.strptime(time_Vap_first,'%Y-%m-%d %H:%M:%S')
		time_Vap_dt = []
		time_Vap_el_mins = []

		time_Vin_first = str(time_Vin[0])
		print("time_Vin_first=",time_Vin_first )
		time_Vin_last = str(time_Vin[-1])
		# if n==1:
		# 	print("time_Vin_last=",time_Vin_last )
		first_time_Vin = datetime.datetime.strptime(time_Vin_first,'%Y-%m-%d %H:%M:%S')
		time_Vin_dt = []
		time_Vin_el_mins = []
		eltime_mins = []



		for t in time_Vap:
			t=str(t)
			datime=datetime.datetime.strptime(t,'%Y-%m-%d %H:%M:%S')
			elapsed = datime- first_time_Vap
			time_Vap_dt.append(datime)#.time)
			time_Vap_el_mins.append((elapsed.total_seconds())/60) #Convert elapsed time from seconds to minutes
		for t in time_Vin:
			t=str(t)
			datime=datetime.datetime.strptime(t,'%Y-%m-%d %H:%M:%S')
			elapsed = datime- first_time_Vin
			time_Vin_dt.append(datime)#.time)
			time_Vin_el_mins.append((elapsed.total_seconds())/60) #Convert elapsed time from seconds to minutes
		for t in time_T1:
			t=str(t)
			datime=datetime.datetime.strptime(t,'%Y-%m-%d %H:%M:%S')
			elapsed = datime - first_time_T1
			time_T1_dt.append(datime)#.time)
			time_T1_el_mins.append((elapsed.total_seconds())/60) #Convert elapsed time from seconds to minutes
		for t in time_P:
			t=str(t)
			datime=datetime.datetime.strptime(t,'%Y-%m-%d %H:%M:%S')
			elapsed = datime - first_time_P
			time_P_dt.append(datime)#.time)
			time_P_el_mins.append((elapsed.total_seconds())/60) #Convert elapsed time from seconds to minutes
		for t in abstime:
			t = t-startime
			t = t/60
			eltime_mins.append(t)


		Nmax = max(and2)
		Nmin = min(and2)
		print(Nmax)
		print(Nmin)


		visibility = (Nmax - Nmin)/(Nmax + Nmin)
		print("Visibility: ", visibility)
		print("")


		for i in range(len(Vap)):
			Rt_Vap = Vap[i]*R0/(V0-Vap[i])
			t = beta/(math.log(Rt_Vap/rInf))
			T_Vap.append(t-273.15)
			Rt_Vin = Vin[i]*R0/(V0-Vin[i])
			t = beta/(math.log(Rt_Vin/rInf))
			T_Vin.append(t-273.15)



		#Stacked plot of all data

		fig, axs = plt.subplots(6,1, num=238, sharex = True)
		xmin=time_Vap_el_mins[0] #40
		xmax=705#time_Vap_el_mins[-1] #60
		#Vap
		axs[0].plot(time_Vap_el_mins, T_Vap,  linestyle = 'none', marker = '.', markersize = 2)
		axs[0].set_ylabel(r"$T_{set}$ ($\degree$C)")
		axs[0].grid()


		#Temp
		axs[1].plot(time_T1_el_mins, T1,  linestyle = 'none', marker = '.', markersize = 2)
		axs[1].set_ylabel(r"T ($\degree C$)")
		axs[1].grid()

		#Power
		axs[2].plot(time_P_el_mins, P,  linestyle = 'none', marker = '.', markersize = 2)
		axs[2].set_ylabel(r"P ($\mu$W)")
		axs[2].grid()


		#and1
		axs[3].plot(eltime_mins, and1,  linestyle = 'none', marker = '.', markersize = 2)
		axs[3].set_ylabel("and1")
		axs[3].grid()

		#and2
		axs[4].plot(eltime_mins, and2,  linestyle = 'none', marker = '.', markersize = 2, label = "Visibility = {:.2f}".format(visibility))
		axs[4].set_ylabel("and2")
		axs[4].legend()
		axs[4].grid()

		#and3
		axs[5].plot(eltime_mins, and3,  linestyle = 'none', marker = '.', markersize = 2)
		axs[5].set_ylabel("and3")
		axs[5].grid()

		axs[5].set_xlim(xmin, xmax)
		fig.suptitle("Coincidences from \n"+str(time_Vap[0]+datetime.timedelta(minutes=xmin))+" to "+str(time_Vap[0]+datetime.timedelta(minutes=xmax)))
		plt.xlabel('Elapsed time (min)', fontsize =16)
		plt.savefig(figname)

		plt.show()



except KeyboardInterrupt:
	print("")
	print("time_T1_last=",time_T1_last )
	print("time_P_last=",time_P_last )
	print("time_Vap_last=",time_Vap_last )
	print("time_Vin_last=",time_Vin_last )
	db.close()
