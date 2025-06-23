#!/usr/bin/env python
#raspistill --timelapse 200 -t 3000000 -n --exposure sport -e jpg --thumb 80:45:15 -o /run/shm/image.jpg --width 640 --height 360 >/dev/null 2>&1 &


import cv2 as cv
import numpy as np
import time
import sys
import os
import subprocess
import json
import shutil
from collections import deque

#path="/home/pi/dev/Grasdetection/bilder/"
#picture = "Bild_1.jpg"

path="/dev/shm/"
picture="image.jpg"

fake=False

valpos=[(285,300),(50,300),(500,300),(285,220),(50,220),(500,220),(285,120)]   # schrift position für Frame 1
hsvpos=[(280,265),(30,265),(490,265),(280,180),(30,180),(490,180),(280,140)]   # schrift position für Frame 1
framepos_p1=[(200,240),(3,240),(440,240),(200,160),(3,160),(440,160),(0,0)]
framepos_p2=[(440,357),(200,357),(637,357),(440,240),(200,240),(637,240),(0,0)]
sizes=[120*239,120*200,120*199,80*239,80*200,80*199,79*240] # sind die flächen der frames
#lower=np.array([0, 110, 0])
#upper = np.array([141, 253, 255])
# Nur "grüner" Bereich im HSV (Hue ~ 35-85°)
lower = np.array([28, 80, 40])
upper = np.array([85, 255, 255])
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
        self.Frame7=self.img[80:159, 201:440]    # [20:159, 0:640]
        self.frameWert=["","","","","","",""]
        self.hsv=[None]*7
        self.dist_left=0
        self.dist_right=0
        self.edge=[0.0,0.0]
        self.edge_result=""
        self.fahrbefehl=["","Wenden","Korrektur rechts", "Korrektur links","","","","","","",""]
        self.width=bild.shape[1]
        self.height=bild.shape[0]
        self.peri=[0,0]
        self.event="Wire "
        self.wire_val=0
        self.distance=["",""]
        self.obstical=10
        self.startdecode=0.0
        self.store=False
        self.kurs=""



def putImageInfo():
    # Hier werden alle Informationen der Bild klasse in das Bild eingeblendet
    # das tritt dann ein, wenn bild.store==True ist

    h, w, _ = bild.img.shape
    l=bild.distance[0]
    r=bild.distance[1]

    # Kurs und Abstände der ToFs oben einblenden

    (text_width, text_height), _ = cv.getTextSize(bild.kurs, cv.FONT_HERSHEY_SIMPLEX, 1, 2)
    x = int((640 - text_width) / 2)
    textsize = cv.getTextSize(str(r)+ 'cm ', cv.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
    bild.img = cv.putText(bild.img, str(l)+ 'cm ', (10,30), cv.FONT_HERSHEY_SIMPLEX , 1, (255,255,255), 2, cv.LINE_AA)
    bild.img = cv.putText(bild.img, bild.kurs,(x,30),cv.FONT_HERSHEY_SIMPLEX , 1, (255,255,255), 2, cv.LINE_AA)
    bild.img = cv.putText(bild.img, str(r)+ 'cm ', (bild.width-textsize[0],30), cv.FONT_HERSHEY_SIMPLEX , 1, (255,255,255), 2, cv.LINE_AA)

    # rectangle für das Datum
    cv.rectangle(bild.img, (200, h - 50), (440, h-4), (200, 200, 200), thickness=-1)
    # rectangle für die unteren Statuszeile
    cv.rectangle(bild.img, (0, h - 30), (w, h-4), (200, 200, 200), thickness=-1)

    bild.img = cv.putText(bild.img, f"L:{bild.edge[0]:.1f}%", (40, 351), cv.FONT_HERSHEY_SIMPLEX , 0.5, (0,0,0),1,cv.LINE_AA)
    bild.img = cv.putText(bild.img, f"R:{bild.edge[1]:.1f}%", (540, 351), cv.FONT_HERSHEY_SIMPLEX , 0.5, (0,0,0),1,cv.LINE_AA)
    hinweis= f"{bild.event} {bild.fahrbefehl[bild.obstical]}"
    (text_w, text_h), _ = cv.getTextSize(hinweis, cv.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    datum= time.strftime("%H:%M:%S  %d.%m.%Y")
    textsize= cv.getTextSize(datum, cv.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
    cv.putText(bild.img, datum, ((int(bild.width/2))-int((textsize[0]/2)),330), cv.FONT_HERSHEY_SIMPLEX , 0.5, (0,0,0), 1, cv.LINE_AA)
    cv.putText(bild.img, hinweis, ((int(bild.width/2))-int((text_w/2)),351), cv.FONT_HERSHEY_SIMPLEX , 0.5, (0,0,0), 1, cv.LINE_AA)

    # Perimeter Werte einblenden

    cv.circle(bild.img, (610, 312), 16, (0, 0, 0), 2, lineType=cv.LINE_AA)
    #cv.circle(bild.img,(610,312), 13, (0,255,0), -1)
    cv.circle(bild.img, (30, 312), 16, (0, 0, 0), 2, lineType=cv.LINE_AA)
    #cv.circle(bild.img,(30,312), 13, (0,255,0), -1)
    if bild.peri[0]==1:
        cv.circle(bild.img,(30,312), 13, (0,128,255), -1)  # orange
    elif bild.peri[0]==2:
        cv.circle(bild.img,(30,312), 13, (0,0,255), -1)  # rot
    else:
        cv.circle(bild.img,(30,312), 13, (0,255,0), -1)   # grün

    if bild.peri[1]==1:
        cv.circle(bild.img,(610,312), 13, (0,128,255), -1) # orange
    elif bild.peri[1]==2:
        cv.circle(bild.img,(610,312), 13, (0,0,255), -1) # rot
    else:
        cv.circle(bild.img,(610,312), 13, (0,255,0), -1)   # grün

    # Frame Information einblenden
    i = 0
    for i in range(0,7):
        bild.img = cv.putText(bild.img, f"[{int(np.mean(bild.hsv[i][:,:,0]))},{int(np.mean(bild.hsv[i][:,:,1]))},{int(np.mean(bild.hsv[i][:,:,2]))}]", hsvpos[i], cv.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        bild.img = cv.putText(bild.img, f"{bild.frameWert[i]}%", valpos[i], cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)
        cv.rectangle(bild.img, framepos_p1[i], framepos_p2[i], color=(0,0,255), thickness=2)


    # das Bild nun abspeichern

    cv.imwrite(archive+"stops_"+str(cnt)+".jpg", bild.img)


def edgeanlize(image):
    # diese Funktion untersucht die unteren beiden Bildhälften auf
    # kanten. ist der Kantenanteil zu groß, dann handelt es sich nicht
    # um Rasen sondern eher um was anderes, Busch / Strauch oder so.
    # habe ich aber noch nicht Scharf geschaltet, muss ich noch testen
    # Graustufen und Weichzeichnen
    #h, w, _ = bild.img.shape
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    blurred = cv.GaussianBlur(gray, (5, 5), 0)

    # Canny auf GANZE untere Bildhälfte – optional zur Anzeige
    # edges_full = cv.Canny(blurred[160:360, :], 130, 290)

    # Region 1 = links, Region 2 = rechts
    region1 = blurred[160:360, 0:320]
    region2 = blurred[160:360, 321:640]

    # Canny pro Region
    edges1 = cv.Canny(region1, 130, 290)
    edges2 = cv.Canny(region2, 130, 290)

    # Kantenanzahl / Pixeldichte
    total_pixels = 320 * 200  # Region-Größe
    edge_percent1 = (cv.countNonZero(edges1) / total_pixels) * 100
    edge_percent2 = (cv.countNonZero(edges2) / total_pixels) * 100
    bild.edge[0]= edge_percent1
    bild.edge[1]= edge_percent2

    # Entscheidungslogik
    '''
    if edge_percent1 > 1.0 and edge_percent2 > 1.0:
        decision = "turn"
    elif edge_percent1 > 1.0:
        decision = "right"
    elif edge_percent2 > 1.0:
        decision = "left"
    else:
        decision = "forward"
    '''
    #print(f"Die Entscheidung gemäß Kantenanalyse Links {edge_percent1:.1f}%, Rechts {edge_percent2:.1f}% => {decision}")
    # Optional Debuganzeige ins Bild schreiben

    return #decision, image
 
def framecalc(frame, i):

    ### Hier werden die Grünanteile der  7 Frames berechnet

    # History-Reset
    if os.path.exists("/run/shm/visual_history"):
        for q in frame_history:
            q.clear()
        #print("History Frames wurden gelöscht")
        os.remove("/run/shm/visual_history")

    # HSV & Maske
    #lower = np.array([0, 110, 0])
    #upper = np.array([141, 253, 255])
    # von KI Nur "grüner" Bereich im HSV (Hue ~ 35-85°) ich habe es bei meinem Rasen auf 28 - 85 korrigiert
    lower = np.array([28, 80, 40])
    upper = np.array([85, 255, 255])
    bild.hsv[i] = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    mask = cv.inRange(bild.hsv[i], lower, upper)
    #bild.hsv[i]=hsv

    # Grünanteil ermitteln
    green_ratio = cv.countNonZero(mask) / sizes[i]
    percent_green = round(green_ratio * 100, 1)
    #print(percent_green)

    # Umgebung einlernen, wenn normale Fahrt startet
    if not os.path.exists("/run/shm/visual_history") and i <= 2:
        #print("Historie Frame wird angelernt")
        env_green.append(percent_green)

    # Adaptiver Schwellenwert
    base_thresh = 30
    min_thresh = 20
    if len(env_green) >= 10:
        avg_env = sum(env_green) / len(env_green)
        threshhold = max(min_thresh, min(base_thresh, avg_env * 0.75))
    else:
        threshhold = base_thresh

    # Historie aktualisieren
    frame_history[i].append(percent_green)
    avg_green = sum(frame_history[i]) / len(frame_history[i])

    # Bild speichern, wenn kritisch (nur bei F1–F3)
    #if i <= 2 and avg_green < threshhold:
    #    bild.store = True

    # Ausgabe
    bild.frameWert[i] = percent_green

def getKurs():
    # holt den Kompasswert aus der Datei wird zum Einblenden oben in der Mitte benötigt
    n=0
    kurs=0
    while True:
        try:
            with open("/dev/shm/kurs.txt", "r") as f:
                tmp=f.read()
                tmp=tmp.strip()
            #print(tmp)
            tmp=tmp.replace("Kurs :","")
            bild.kurs=tmp+ " Grad"
            break
        except:
            n+=1
            log("Fehler beim lesen von Kurs.txt")
            if n>5:
                tmp=None
                bild.kurs=""
                break
    return bild.kurs


def mergeDistance():
    # holt die Werte der ToFs wird zur einblendung oben Lnks und rechts benötigt
    getKurs()
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
            l=obj.get("left")
            r=obj.get("right")
            if l> 200:
                l=200
            if r> 200:
                r=200    
        except:
            pass
        #print(l,r)
        bild.distance[0]=l
        bild.distance[1]=r

        """
        Die store_img wurde von Laser.py erstellt wenn die Dsatnce zu gering ist
        """
        if os.path.isfile("/run/shm/store_img"):
            with open("/run/shm/store_img","r") as f:
                content = f.read()
                #print(f"Contenten von wire_img {content}")
                try:
                    val=int(content)
                except:
                   val=10

            bild.event="Laser "
            bild.laser=True
            bild.store=True
            bild.obstical=val
            #print(f"Event = {bild.event} Bild Store = {bild.store} Ausweichen mit = {bild.fahrbefehl[bild.obstical]}")
            
def mergePeri():
    # holt die Perimeter Statis, wird zum einblenden unten links und rechts benötigt

    if os.path.isfile("/run/shm/wire.img_data")==True:
        try:
            with open("/run/shm/wire.img_data", 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
                data= None
    if data:
        #if debug:
        #    print(data)
        if data.get("left_state")=="near":
            bild.peri[0]=1
        elif data.get("left_state")=="outside":
            bild.peri[0]=2
        else:
            bild.peri[0]=0

        if data.get("right_state")=="near":
            bild.peri[1]=1
        elif data.get("right_state")=="outside":
            bild.peri[1]=2
        else:
            bild.peri[1]=0

        val= data.get("frame")

        if val < 10:
            bild.store=True
            bild.event="Wire "
            bild.obstical=val


def analyze_image(frameWerte, THRESHOLD):
    #   F1   F2  F3  F4  F5  F6  F7
    #    0    1   0   0   1   0   0        =>  36  rechts ausweichen
    #    0    1   0   0   1   0   0        => 100  rechts ausweichen
    #    1    1   1   0   1   0   0        => 116  rechts ausweichen
    #    0    0   1   0   0   1   0        =>  18  links  ausweichen
    #    1    0   1   0   0   1   0        =>  82  links  ausweichen
    #    0    1   1   0   0   1   0        =>  50  links  ausweichen
    #    1    1   1   1   0   0   0        => 120  wenden
    #    1    1   1   1   0   0   1        => 121  wenden
    #    1    1   1   1   1   1   0        => 126  wenden
    #    1    1   1   1   1   1   1        => 127  wenden


    entscheidungen ={
        36:  "nach rechts",
        100: "nach rechts",
        116: "nach rechts",
        124: "nach rechts",
        18:  "nach links",
        82:  "nach links",
        50:  "nach links",
        122: "nach links",
        120: "wenden",
        121: "wenden",
        126: "wenden",
        127: "wenden",
        }

    # 3. In 0 = OK / 1 = Problem umwandeln
    #print(frameWerte)
    frameZustand = [1 if wert < THRESHOLD else 0 for wert in frameWerte]

    # Konvertiere den Zustand in einen String aus 0/1
    bin_str = ''.join(str(bit) for bit in frameZustand)

    # Binärstring in Integer umwandeln
    zustandswert = int(bin_str, 2)
    aktion = entscheidungen.get(zustandswert,"nothing to do")     # "nothing to do" tritt dann ein, wenn der zustandswert nicht in Entscheidungen vorhanden wäre
    #print(aktion)
    if aktion=="nothing to do":
        #bild.store=True
        return 10
    elif aktion == "wenden":
        log(str(time.strftime('%H:%M:%S'))+" Frame Binär Analyse "+ bin_str + " Dezimal Wert = " + str(zustandswert))
        bild.store=True
        return 1
    elif aktion == "nach links":
        log(str(time.strftime('%H:%M:%S'))+" Frame Binär Analyse "+ bin_str + " Dezimal Wert = " + str(zustandswert))
        bild.store=True
        return 3
    elif aktion == "nach rechts":
        log(str(time.strftime('%H:%M:%S'))+" Frame Binär Analyse "+ bin_str + " Dezimal Wert = " + str(zustandswert))
        bild.store=True
        return 2

def imgdecode():
    global cnt
    hasVal = []
    bild.store=False
    bild.original=bild.img.copy()
    mergeDistance()
    edgeanlize(bild.img)
    mergePeri()
    #print(f"Bild Obstical 340 {bild.obstical}")
    frames=[bild.Frame1,bild.Frame2,bild.Frame3,bild.Frame4,bild.Frame5,bild.Frame6, bild.Frame7]
    for i in range (0,7):
        framecalc(frames[i],i)

    #Mittelwert von der Helligkeit von Frame 1 und Frame 4 berechnen
    mean_ref_v = (bild.hsv[0][:, :, 2].mean() + bild.hsv[3][:, :, 2].mean()) / 2
    #print(f"Mittelwert von frame 1 und Frame 3 = {mean_ref_v}")

    if bild.frameWert[0] > threshhold and  bild.frameWert[3] > threshhold and bild.frameWert[6] < threshhold:
        # wenn die Bildhelligkeit von Frame 7 viel größer ist als von
        # frame 1 und Frame 4 dann liegt es nahe dass er aus dem Schatten in die
        # Sonne fährt, und dann muss der Grünanteil für frame 7 angepasst werden
        if bild.hsv[6][:, :, 2].mean() - mean_ref_v > 25:
            bild.frameWert[6] = bild.frameWert[6] + 20
            log(f"{time.strftime('%H:%M:%S')} Korrektur erforderlich, Diff. ist {round((bild.hsv[6][:, :, 2].mean() - mean_ref_v),2)} Neuer Framewert von 7 ist {bild.frameWert[6]}" )
            #print(f"Korrektur Framewert ist {bild.frameWert[6]}")
            #bild.obstical = 10

    if bild.obstical == 10:
        bild.obstical= analyze_image(bild.frameWert, threshhold)
        if bild.obstical < 10:
            bild.event="PiCAM "

    #if debug:
    #    bild.store= True

    if bild.store==True:

        cv.imwrite(archive+"picam_"+str(cnt)+".jpg", bild.original)
        putImageInfo()

        with open("/run/shm/Mower_visual","w") as f:
            f.write(str(bild.obstical))
        tmp=str(bild.frameWert).replace("'","")
        with open("/run/shm/Visual_Frames","w") as f:
            f.write(tmp)    
        #print(tmp)
        log(str(time.strftime('%H:%M:%S')+" Bild "+ archive+"stops_"+str(cnt)+".jpg abgespeichert und Mower_visual mit "+ str(bild.obstical)+ " erstellt"))
        #print("Frame Werte= "+  bild.frameWert[0]+ '% ' + bild.frameWert[1]+ '% '+  bild.frameWert[2]+ '% '+ bild.frameWert[3]+ '% '+ bild.frameWert[4]+ '% '+ bild.frameWert[5]+ '% ' )         
        cnt+=1
                 
n=0
oldstamp=time.time()
# Initialisierung
frame_history = [deque(maxlen=5) for _ in range(7)]
env_green = deque(maxlen=30)

while True:
     ## Hier wird ein Fake grünes Bild in die Ram Disk gestellt
     ## wenn ich den Mower auf dem Teststand betreibe

     if os.path.isfile("/run/shm/fakelawn")==True:
         if os.path.isfile("/home/pi/Mower/archive/images/image.jpg")==True:
             os.system("cp /home/pi/Mower/archive/images/image.jpg /dev/shm/image.jpg")
             fake=True
     else:
         fake=False
     if os.path.exists(path+picture):             
        timestamp = os.path.getmtime(path+picture)
     if time.time()-timestamp > 1 and fake == False:
         subprocess.call("/home/pi/Mower/bin/piCAM.sh",shell=True)
         time.sleep(0.5)
         log(str(time.strftime('%H:%M:%S')+" raspistill wurde erneut gestartet"))
         
     if timestamp != oldstamp and os.path.isfile(path+picture) and os.path.isfile("/run/shm/Mower_visual")==False:
           #print("geht los")
           img=cv.imread(path+picture)
           bild=Bild(img)
           bild.frameWert = [0] * 7  # Werte für F1 bis F7
           bild.startdecode=time.time()
           imgdecode()
           oldstamp=timestamp
           #print("Dauer der Decodierung= "+ str(time.time()-bild.startdecode))
     time.sleep(0.100)

sys.exit()

