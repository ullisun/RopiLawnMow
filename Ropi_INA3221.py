#!/usr/bin/env python
#
# Test SDL_Pi_INA3221
# John C. Shovic, SwitchDoc Labs
# 03/05/2015
#
# source https://github.com/semaf/INA3221-Python-Library

# imports

import sys
import os
import time
import datetime
import random 
import SDL_Pi_INA3221
from gpiozero import LED
buzzer=LED(7)
buzzer.off()
debug=False

def beep():
    i=0
    while i<4:
        buzzer.on()
        time.sleep(0.1) 
        buzzer.off()
        time.sleep(0.2)
        i+=1

# check if /home/pi/RopiLawnMow/debug.txt exists

if os.path.isfile("/home/pi/RopiLawnMow/debug.txt"):
    debug=True


if debug:
    print("")
    print("Program Started at:"+ time.strftime("%Y-%m-%d %H:%M:%S"))
    print("")



path="/home/pi/RopiLawnMow/data/"
filename = time.strftime("%Y-%m-%d") + "RopiCurrentData.txt"
if os.path.isdir(path)==False:
    os.makedirs(path)
    

starttime = datetime.datetime.utcnow()
ina3221 = SDL_Pi_INA3221.SDL_Pi_INA3221(addr=0x40)

# the three channels of the INA3221
MotorRightChannel  = 1
MotorLeftChannel   = 2
MotorCutterChannel = 3

scantime=time.time()
while True:
    if time.time()-scantime>=2:
        shuntvoltage1 = 0
        busvoltage1   = 0
        current_mA1   = 0
        loadvoltage1  = 0

        busvoltage1 = ina3221.getBusVoltage_V(MotorRightChannel)
        shuntvoltage1 = ina3221.getShuntVoltage_mV(MotorRightChannel)
        current_mA1 = ina3221.getCurrent_mA(MotorRightChannel)  
        loadvoltage1 = busvoltage1 + (shuntvoltage1 / 1000)

        shuntvoltage2 = 0
        busvoltage2 = 0
        current_mA2 = 0
        loadvoltage2 = 0
   
        busvoltage2 = ina3221.getBusVoltage_V(MotorLeftChannel)
        shuntvoltage2 = ina3221.getShuntVoltage_mV(MotorLeftChannel)
        current_mA2 = ina3221.getCurrent_mA(MotorLeftChannel)
        loadvoltage2 = busvoltage2 + (shuntvoltage2 / 1000)
    
        shuntvoltage3 = 0
        busvoltage3 = 0
        current_mA3 = 0
        loadvoltage3 = 0
    
        busvoltage3 = ina3221.getBusVoltage_V(MotorCutterChannel)
        shuntvoltage3 = ina3221.getShuntVoltage_mV(MotorCutterChannel)
        current_mA3 = ina3221.getCurrent_mA(MotorCutterChannel)
        loadvoltage3 = busvoltage3 + (shuntvoltage3 / 1000)
        if debug:
            print("----------------------------------------------")
            print("Aktuelle Zeit: ",time.strftime("%Y-%m-%d %H:%M:%S"))
            print("----------------------------------------------")
            print("")
            print("Spannung am INA Modul:  %3.2f V" % loadvoltage1)
            print("Spannung am rechten Motor: %3.2f V " % busvoltage1)
            print("Stromaufnahme rechter Motor:  %3.2f mA" % current_mA1)
            print("")
            print("Spannung am linken Motor:  %3.2f V " % busvoltage2)
            print("Stromaufnahme linker Motor:  %3.2f mA" % current_mA2)
            print("")
            print("Spannung am Cutter Motor :  %3.2f V " % busvoltage3)
            print("Stromaufnahme Cutter Motor:  %3.2f mA" % current_mA3)

        #Example String=  0.0;19.12;0
        outputPiMow="0.0;"+str(round(loadvoltage1,2))+";0"
        
        #                 Time    ; VBat; IMR; IML; IMC         VBat= Votage Akku; IMR= Current Motor Right; IML= Current Motor Left; IMC= Current Motor Cutter;  
        #Example String=  19:26:57;19.12;32.8;28.8;2.8
        outputRopi=time.strftime("%H:%M:%S")+";"+str(round(loadvoltage1,2))+";"+str(round(current_mA1,2))+";"+str(round(current_mA2,2))+";"+str(round(current_mA3,2))+"\n"
         
        with open("/run/shm/.PiMowBot.battery","w") as f:
            f.write(outputPiMow)
        with open(path+filename,"a") as f:
            f.write(outputRopi)
    
        if loadvoltage1 <=19:
            beep()
        scantime=time.time()   
    time.sleep(0.5)
