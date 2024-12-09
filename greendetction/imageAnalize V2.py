#!/usr/bin/env python
#raspistill --timelapse 200 -t 3000000 -n --exposure sport -e jpg --thumb 80:45:15 -o /run/shm/image.jpg --width 640 --height 360 >/dev/null 2>&1 &
import cv2 as cv
import numpy as np
import time
import sys
import os
import subprocess
import json
#path="/home/pi/dev/Grasdetection/bilder/"
#picture = "Bild_1.jpg"
# For development reasons create the file with echo "" > /run/shm/fakelawn
# and make shure that the image.jpg of this github folder https://github.com/ullisun/RopiLawnMow/edit/main/greendetction
# is located in /home/pi/Mower/archive/images/.
# Then you are able to test the other sensors in your test envoriment no lawn is needed.


path="/dev/shm/"
picture="image.jpg"

fake=False

valpos=[(250,300),(50,300),(500,300),(250,200),(50,200),(500,200)]   # schrift position für Frame 1
framepos_p1=[(160,240),(3,240),(440,240),(160,160),(3,160),(440,160)]
framepos_p2=[(440,357),(160,357),(637,357),(440,240),(160,240),(637,240)]
sizes=[120*239,120*200,120*199,80*239,80*200,80*199]
lower=np.array([0, 110, 0])
upper = np.array([141, 253, 255])
threshhold=30
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

nfiles=os.listdir(archive)
cnt=len(nfiles)
if cnt==0:
    cnt=cnt+10000
else:
    try:
        nfiles.sort()
        tmp=nfiles[len(nfiles)-1]
        tmp=tmp.replace("stops_","")
        tmp=tmp.replace(".jpg","")
        cnt=int(tmp)+1
    except:
        cnt=20000
         
            

if os.path.isfile("/run/shm/Mower_visual"):
    os.remove("/run/shm/Mower_visual")


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
        self.width=bild.shape[1]
        self.height=bild.shape[0]
        self.peri=["",""]
        self.distance=["",""]
        self.obstical=10
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


def mergeDistance():
    l=0
    r=0
    content='{"left":200,"right":200}'    # normaler Datei Inhalt= {"left":25,"right":25}
    if os.path.isfile("/run/shm/distance"):
        with open("/run/shm/distance","r") as f:
            content=f.read()
            #print(content)
        try:   
            obj=json.loads(content)
            #print(obj)
            l=int(obj["left"])
            r=int(obj["right"])
            if l> 200:
                l=200
            if r> 200:
                r=200    
        except:
            pass
        #print(l,r)    
        textsize = cv.getTextSize(str(r)+ 'cm ', cv.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
        bild.img = cv.putText(bild.img, str(l)+ 'cm ', (10,30), cv.FONT_HERSHEY_SIMPLEX , 1, (255,255,255), 2, cv.LINE_AA)
        bild.img = cv.putText(bild.img, str(r)+ 'cm ', (bild.width-textsize[0],30), cv.FONT_HERSHEY_SIMPLEX , 1, (255,255,255), 2, cv.LINE_AA)
               
        if os.path.isfile("/run/shm/store_img"):
            bild.store=True           
            
def mergePeri():
    content="0"
    cv.circle(bild.img,(610,330), 16, (0,0,0), -1)
    cv.circle(bild.img,(610,330), 13, (0,255,0), -1)
    cv.circle(bild.img,(30,330), 16, (0,0,0), -1)
    cv.circle(bild.img,(30,330), 13, (0,255,0), -1)
    if os.path.isfile("/run/shm/wire_img")==True:
        with open("/run/shm/wire_img","r") as f:
            content = f.read()
            try:
                val=int(content)
            except:
                val=0
        if val == 1:
            cv.circle(bild.img,(30,330), 14, (0,0,255), -1)
            cv.circle(bild.img,(610,330), 14, (0,0,255), -1)
        elif val== 2:
            cv.circle(bild.img,(30,330), 14, (0,0,255), -1)    
        elif val== 3:
            cv.circle(bild.img,(610,330), 14, (0,0,255), -1)    
        bild.store=True            


def imgdecode():
    global cnt
    bild.store=False
    bild.original=bild.img.copy()
    mergeDistance()
    mergePeri()    
    frames=[bild.Frame1,bild.Frame2,bild.Frame3,bild.Frame4,bild.Frame5,bild.Frame6]
    for i in range (0,6):
        framecalc(frames[i],i)
    
    if bild.store==True:
        if float(bild.frameWert[1])<=threshhold:
            bild.obstical=2
        if float(bild.frameWert[2])<=threshhold:
            bild.obstical=3            
        if float(bild.frameWert[0])<=threshhold:
            bild.obstical=1
        #cv.imwrite(archive+"picam_"+str(cnt)+".jpg", bild.original)    
        #speicher das aktuelle Bild
        
        datum= time.strftime("%H:%M:%S  %d.%m.%Y")  
        textsize= cv.getTextSize(datum, cv.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        cv.putText(bild.img, datum, ((int(bild.width/2))-int((textsize[0]/2)),350), cv.FONT_HERSHEY_SIMPLEX , 0.5, (255,255,255), 1, cv.LINE_AA)    
        cv.imwrite(archive+"stops_"+str(cnt)+".jpg", bild.img)
        with open("/run/shm/Mower_visual","w") as f:
            f.write(str(bild.obstical))
        tmp=str(bild.frameWert).replace("'","")    
        with open("/run/shm/Visual_Frames","w") as f:
            f.write(tmp)    
        log(str(time.strftime('%H:%M:%S')+" Bild "+ archive+"stops_"+str(cnt)+".jpg abgespeichert und Mower_visual mit "+ str(bild.obstical)+ " erstellt"))
        #print("Frame Werte= "+  bild.frameWert[0]+ '% ' + bild.frameWert[1]+ '% '+  bild.frameWert[2]+ '% '+ bild.frameWert[3]+ '% '+ bild.frameWert[4]+ '% '+ bild.frameWert[5]+ '% ' )         
        cnt+=1
                 
n=0
oldstamp=time.time()
while True:
     ## Hier wird ein Fake grünes Bild in die Ram Disk gestellt
     if os.path.isfile("/run/shm/fakelawn")==True:
         if os.path.isfile("/home/pi/Mower/archive/images/image.jpg")==True:
             os.system("cp /home/pi/Mower/archive/images/image.jpg /dev/shm/image.jpg")
             fake=True
     else:
         fake=False         
     timestamp = os.path.getmtime(path+picture)
     if time.time()-timestamp>1 and fake == False:
         subprocess.call("/home/pi/Mower/bin/piCAM.sh",shell=True)
         time.sleep(0.5)
         log(str(time.strftime('%H:%M:%S')+" raspistill wurde erneut gestartet"))
         
     if timestamp != oldstamp and os.path.isfile("/run/shm/Mower_visual")==False:
           img=cv.imread(path+picture)
           bild=Bild(img)
           bild.startdecode=time.time()
           imgdecode()
           oldstamp=timestamp
           #print("Dauer der Decodierung= "+ str(time.time()-bild.startdecode))
     time.sleep(0.100)

sys.exit()

