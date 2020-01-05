"""
Code for controlling the variable delay line (VDL) using the serial package.
Reads VDL setpoint from table in the FQNET GUI database every second and
updates the VDL.
"""

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
#import pyvisa
#import matplotlib.pyplot as plt
import pymysql
import matplotlib as mpl
import serial

#Command to set directory for saving figures produced by this script
mpl.rcParams["savefig.directory"] = os.chdir(os.path.dirname("/home/inqnet4/Desktop/CQNET/EntSource"))

#Connect to vdl
ser = serial.Serial(
	port='/dev/ttyUSB0',
	baudrate=9600,
	timeout=None,
)
ser.flushInput()
ser.flushOutput()
ser.isOpen()

#Function to read vdl values from database.
#Very ineffecient-- conencts to data base and
#copies all vdl entries every time it's called.
#Need to figure out how to fetch most recent vdl entry
#with database already open (nontrivial)
def getLastDelay():
	db = pymysql.connect(host="<IP ADDRESS>",  #Replace <IP ADDRESS> with the IP of computer with database. Local host if is same computer.
						 user="<USERNAME>", #Replace <USERNAME> with your username
						 passwd="<PASSWORD>",  #Replace <PASSWORD> with your password
						 db="INQNET_GUI",
						 charset='utf8mb4',
						 cursorclass=pymysql.cursors.DictCursor)
	with db.cursor() as cur:
		TABLE_NAME = "inqnet_gui_tab2gates_V2"
		queryGUI="SELECT delayline FROM "+TABLE_NAME+" ORDER BY id DESC LIMIT 1;"
		cur.execute(queryGUI)
		result=cur.fetchall()
		result=result[0]
		lastDelay=result["delayline"]
	db.close()
	return lastDelay


#Read last delay from table every second. If last delay is different from
#current delay, update current delay on vdl. Otherwise, stay same.
try:
	initDelay=getLastDelay()
	print("Set VDL to {}".format(initDelay))
	cmd = '_ABS_{}$'.format(initDelay)
	ser.write(cmd.encode())
	bytesToRead = ser.inWaiting()
	data = ser.read(bytesToRead)
	print(data.decode())
	currentDelay=initDelay
	while(True):
		currentDelay=getLastDelay()
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
	ser.close()
