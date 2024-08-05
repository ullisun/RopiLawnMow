#!/usr/bin/env python
#raspistill --timelapse 200 -t 3000000 -n --exposure sport -e jpg --thumb 80:45:15 -o /run/shm/image.jpg --width 640 --height 360 >/dev/null 2>&1 &
import cv2 as cv
import numpy as np
import time
import sys
import os
import subprocess
#path="/home/pi/dev/Grasdetection/bilder/"
#picture = "Bild_1.jpg"

path="/dev/shm/"
picture="image.jpg"

valpos=[(250,300),(50,300),(500,300),(250,200),(50,200),(500,200)]   # schrift position für Frame 1
framepos_p1=[(160,240),(3,240),(440,240),(160,160),(3,160),(440,160)]
framepos_p2=[(440,357),(160,357),(637,357),(440,240),(160,240),(637,240)]
sizes=[120*239,120*200,120*199,80*239,80*200,80*199]
lower=np.array([0, 110, 0])
upper = np.array([141, 253, 255])
threshhold=25
debug=False



if len(sys.argv)>=2:
   if (sys.argv[1])=="-d":
        debug=True
else:
   debug=False 

def log(para):
    if debug==True:
        print(para)    
    with open(logfile, "a") as file:
        file.write(para + "\n")


logfolder="/home/pi/Mower/archive/images/logs/"+ str(time.strftime('%Y%m%d'))+"/"
logfile=logfolder+"Bild_Analyse.log"
archive="/home/pi/Mower/archive/images/"+ str(time.strftime('%Y%m%d'))+"/"
if not os.path.isdir(logfolder):
    os.makedirs(logfolder)
    log("Folder " + logfolder + " wurde erstellt")

if not os.path.isdir(archive):
    os.makedirs(archive)
    log("Folder " + archive + " wurde erstellt")
log("Folder " + logfolder + " existiert nun")
log("Folder " + archive + " existiert nun")

cnt=len(os.listdir(archive))
cnt=cnt+10000    

if os.path.isfile("/run/shm/.PiMowBot_visual"):
    os.remove("/run/shm/.PiMowBot_visual")


class Bild:
    def __init__(self,bild):
        self.img=bild      # image welches später abgespeichert wird
        self.original=None
        self.Frame1=self.img[240:360, 201:440]
        self.Frame2=self.img[240:360, 0:200]
        self.Frame3=self.img[240:360, 441:640]
        self.Frame4=self.img[160:239, 201:440]
        self.Frame5=self.img[160:239, 0:200]
        self.Frame6=self.img[160:239, 441:640]
        self.frameWert=["","","","","",""]
        self.obstical=0
        self.startdecode=0.0
        self.store=False


def framecalc(frame,i):
    #sizes=[120*239,120*200,120*199,80*239,80*200,80*199]
    #lower=np.array([0, 110, 0])
    #upper = np.array([141, 253, 255])
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, lower, upper)
    #print(cv.countNonZero(mask))
    no_green = cv.countNonZero(mask)/(sizes[i])
    if round(no_green*100) <= threshhold and i<= 2:
        bild.store=True
    bild.frameWert[i]=str(round(no_green*100,1))
    #print('Ratio of green pixels in Frame'+str(i+1)+' is: ' + bild.frameWert[i]+ '% '+ str(sizes[i]) +' ;'+str(i)) 
    bild.img = cv.putText(bild.img, bild.frameWert[i]+ '% ', valpos[i], cv.FONT_HERSHEY_SIMPLEX , 1, (0,0,0), 2, cv.LINE_AA) 
    cv.rectangle(bild.img,framepos_p1[i],framepos_p2[i],color=(0,0,255),thickness=2)


def mydecode():
    global cnt
    bild.store=False
    bild.original=bild.img.copy()    
    frames=[bild.Frame1,bild.Frame2,bild.Frame3,bild.Frame4,bild.Frame5,bild.Frame6]
    for i in range (0,6):
        framecalc(frames[i],i)
    #print("Frame Werte= "+  bild.frameWert[0]+ '% ' + bild.frameWert[1]+ '% '+  bild.frameWert[2]+ '% '+ bild.frameWert[3]+ '% '+ bild.frameWert[4]+ '% '+ bild.frameWert[5]+ '% ' )    
    if bild.store==True:
        if float(bild.frameWert[1])<=threshhold:
            bild.obstical=2
        if float(bild.frameWert[2])<=threshhold:
            bild.obstical=3            
        if float(bild.frameWert[0])<=threshhold:
            bild.obstical=1
        cv.imwrite(archive+"picam_"+str(cnt)+".jpg", bild.original)    
        cv.imwrite(archive+"frame_"+str(cnt)+".jpg", bild.img)
        with open("/run/shm/.PiMowBot_visual","w") as f:
            f.write(str(bild.obstical))
        log(str(time.strftime('%H:%M:%S')+" Bild "+ archive+"frame_"+str(cnt)+".jpg abgespeichert und .PiMowBot_visual mit "+ str(bild.obstical)+ " erstellt"))
        #print("Frame Werte= "+  bild.frameWert[0]+ '% ' + bild.frameWert[1]+ '% '+  bild.frameWert[2]+ '% '+ bild.frameWert[3]+ '% '+ bild.frameWert[4]+ '% '+ bild.frameWert[5]+ '% ' )         
        cnt+=1
                 
n=0
oldstamp=time.time()
while True:
     timestamp = os.path.getmtime(path+picture)
     if time.time()-timestamp>1:
         subprocess.call("/home/pi/Mower/bin/piCAM.sh",shell=True)
         log(str(time.strftime('%H:%M:%S')+" raspistill wurde erneut gestartet"))
     if timestamp != oldstamp and os.path.isfile("/run/shm/.PiMowBot_visual")==False:
           img=cv.imread(path+picture)
           bild=Bild(img)
           bild.startdecode=time.time()
           mydecode()
           oldstamp=timestamp
           #print("Dauer der Decodierung= "+ str(time.time()-bild.startdecode))
     time.sleep(0.100)

sys.exit()

