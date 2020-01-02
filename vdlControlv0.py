import requests
import ast
from datetime import datetime, timedelta
import time
import numpy as np
import getpass
import os
import subprocess as sp
import socket
import sys
import glob
import subprocess
from subprocess import Popen, PIPE
import pipes
from pipes import quote
import argparse
import pyvisa
import matplotlib.pyplot as plt
import pymysql
import matplotlib as mpl
import serial

mpl.rcParams["savefig.directory"] = os.chdir(os.path.dirname("/home/inqnet4/Desktop/CQNET/EntSource"))

db = pymysql.connect(host="192.168.0.125",
						 user="INQNET4",
						 passwd="Teleport1536!",  # your password
						 db="INQNET_GUI",
						 charset='utf8mb4',
						 cursorclass=pymysql.cursors.DictCursor)
#and1=[]
#and2=[]
#and3=[]
#time_GUI=[]
#delayline=[]
# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial(
	port='/dev/ttyUSB0',
	baudrate=9600,
	timeout=None,
)
ser.flushInput()
ser.flushOutput()
ser.isOpen()

try:
	with db.cursor() as cur:
		#lastid= cur.lastrowid
		#print(lastid)

		TABLE_NAME = "inqnet_gui_tab2gates_V2"
		#queryGUI="SELECT delayline FROM "+TABLE_NAME+" ORDER BY id DESC LIMIT 1;"
		#queryGUI="SELECT delayline FROM "+TABLE_NAME+" where id = "+str(lastid)+";"
		#queryGUI= "SELECT LAST_INSERT_ID(delayline) FROM "+TABLE_NAME+";"
		queryGUI= "SELECT max(id) from "+TABLE_NAME+";"
		#queryGUI="SELECT LAST_INSERT_ID()"
		cur.execute(queryGUI)
		result=cur.fetchall()
		print(result)
		#result=result[0]
		initDelay=result["delayline"]
		print("Set VDL to {}".format(initDelay))
		cmd = '_ABS_{}$'.format(initDelay)
		ser.write(cmd.encode())
		bytesToRead = ser.inWaiting()
		data = ser.read(bytesToRead)
		print(data.decode())
		while(True):
			lastid=db.insert_id()#cur.lastrowid
			queryGUI="SELECT delayline FROM "+TABLE_NAME+" where id = "+str(lastid)+";"
			cur.execute(queryGUI)
			result=cur.fetchall()
			result=result[0]
			currentDelay=result["delayline"]
			print(currentDelay)
			if(currentDelay!=initDelay):
				print("Set VDL to {}".format(currentDelay))
				cmd = '_ABS_{}$'.format(currentDelay)
				ser.write(cmd.encode())
				bytesToRead = ser.inWaiting()
				data = ser.read(bytesToRead)
				print(data.decode())
				initDelay=currentDelay
			time.sleep(1)
except KeyboardInterrupt:
	print("")
	print("Quit")
	db.close()
	ser.close()
