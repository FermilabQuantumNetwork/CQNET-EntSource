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


ser = serial.Serial(
	port='/dev/ttyUSB0',
	baudrate=9600,
	timeout=None,
)
ser.flushInput()
ser.flushOutput()
ser.isOpen()

def getLastDelay():
	db = pymysql.connect(host="192.168.0.125",
							 user="INQNET4",
							 passwd="Teleport1536!",  # your password
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
