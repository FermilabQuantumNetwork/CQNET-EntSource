#This writes wavelength vs time data from a '.lta' file
#to the database.
#Requirements: Python3, mysql, packages listed below.


import time
import math
import pymysql
import numpy as np
import re
import sys
import datetime
import pandas as pd
from statistics import mean
from itertools import groupby

#Parse data from file
FILENAME="dataTest_Nov21to22.csv"
and1=[]
and2=[]
and3=[]
abstime=[]
with open(FILENAME,'r') as f:
    line = f.readline()
    while line:
        line = f.readline()
        linesplit = line.split(",")
        #linesplit=linesplit[0].split()
        if len(linesplit)>1:
            a1 = float(linesplit[0])
            and1.append(a1)
            a2 = float(linesplit[1])
            and2.append(a2)
            a3 = float(linesplit[2])
            and3.append(a3)
            abs = float(linesplit[3].rstrip())
            abstime.append(abs)

db = pymysql.connect(host="192.168.0.125",  # host pc
		     user="inqnet1",         # this user only has access to CPTLAB database
             password="Teleport1536!",  # your password
		     #auth_plugin='mysql_native_password',
		     database="teleportcommission",
             charset='utf8mb4',
             cursorclass=pymysql.cursors.DictCursor) # name of the data base

TABLE_NAME = "FQNETGUI"

try:
    #Create mysql cursor
    with db.cursor() as cur:
        line = '  ID  |   and1   |   and2   |   and3   |   abstime   '.format(*range(4))
        print(line)
        for i in range(len(abstime)):
            a1_str=str(and1[i])
            a2_str = str(and2[i])
            a3_str = str(and3[i])
            abs_str = str(abstime[i])
            query = "INSERT INTO "+TABLE_NAME+"(and1, and2, and3, abstime) values(%s, %s, %s, %s);"
            cur.execute(query,(a1_str,a2_str, a3_str, abs_str))

    db.commit()
finally:
    db.close()
