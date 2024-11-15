'''
please note:
This python script is a further development of the BLE-remote control receiver of the PiMowbot SW from
TGD Consulting   http://pimowbot.tgd-consulting.de/

'''

import asyncio
import sys
import os
import bluetooth
import subprocess
from time import sleep, strftime, time
import threading
import signal
from gpiozero import LED
import beeper as piep

'''
cmd=  0.58 118
cmd=  0.51 172
cmd=  0.51 -180
cmd=  0.55 -158
cmd=  0.58 -150
md=  m
Cutter on/ off
cmd=  m
Cutter on/ off
cmd=  cw 0.33
cw  16.5   -16.5
cc  -50.0   50.0
cmd=  cc -1.15
cc  -50.0   50.0
cmd=  cc -1.14

'''

turtle=1
ignition=False
idle=time() # eine Minute idle = PiMowBot PowerSaving Mode
Cutter=LED(5)
BT_LED=LED(1)
sleep(0.1)
Cutter.on() # Weil piMowbot die Werte nach unten zieht wenn Active ist
BT_LED.off()
CUTTER=False # wird benötigt damit der Cutter bei fehlendem BT Signal ausgeht
DRIVE= False # wird benötigt damit der Mäher bei fehlendem BT Signal gestoppt wird

def lg(t):
    print(t)
    logfolder=("/home/pi/Mower/logs/"+ str(strftime('%Y%m%d'))+"/")   
    with open(logfolder+"BT-Remote.log", "a") as f:
        f.write(strftime('%H:%M:%S')+" " + t+"\n")

def reset():
    global scanning, found, RCdevice, AdvService
    scanning=True
    found=False
    RCdevice=None

def exitroutine():
    try:
        BT_LED.off()
        if CUTTER==True:   #Wird nur ausgeschaltet, wenn er per Remote angeschaltet wurde
            Cutter.on()    #Weil piMowbot-SW die Werte nach unten zieht wenn Active ist
        if DRIVE==True:
            stop_drive()    
        client.socket.close()
    except:
        pass
    finally:
        os._exit(0)
    #    print("Programm beendet")



# Handler zur Erkennung von kill SIGTERM und SIGINT
def signal_term_handler(signal, frame):
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_term_handler)

cmd_last=None
ddir=0 # drive direction
drift=1  



def receive():
   while True:
       try:
            state = client_socket.recv(1024)
            data= state.decode("utf-8").strip()
            if len(data)>0:
                #print("Received " + data) 
                #if data.find(" ") != -1:
                #    m=data.split(" ")
                #    print("Data laenge= ",len(m))                   
                drive(data)
                #print("Received ",data)
                #print(data)
       except Exception as err:
           try:
               print(f"Receive: Fehler ist aufgetreten: {err.errno}")
               lg("Receive: Fehler ist aufgetreten "+ str(err.errno))                       
               if err.errno==104:
                    exitroutine()
           except:
               pass
       


async def send_LifeData():
   # hier sollten später Daten gesendet werden die in der APP zu anzeige gebracht werden wie z.B.
   # Akkustand, seit wann der Mäher in Betrieb war, wann das letzt Mal gemäht wurde
   # wieviel Meter der Mäher seit dem letzten Start gelaufen ist
   # ob sich der Messer Motor Dreht
   # protokoll könnte so aussehen:
   #       1       ;  14.5 ;     1  ;   237    ;12.10.13:45;     75   ;823;
   # Battery Sombol;BattSpg;MowMotor; Heading  ; Start     ;  laufzeit;Meter 
   val=0 
   cut=0
   oldkurs=0
   kurs=0
   while True:
        cut=abs(Cutter.value +(-1))    # stellt fest ob der Messer Motor dreht, um dann das passende Flag zu setzen.
        pic="4" 
		  # hier wird der Compass ausgelesen 	
        try:        
            if os.path.isfile("/run/shm/kurs.txt"):
                with open("/run/shm/kurs.txt","r") as f:
                    kurs=f.read()
                    z=kurs.replace("Kurs : ","")
                    kurs=z.strip()
                    kurs=float(kurs)
                    kurs=int(kurs)
                    oldkurs=kurs        
        except:
            kurs=oldkurs	
        #print("CUTTER=", CUTTER)
        val=0
        if os.path.isfile("/run/shm/battery"):
               with open("/run/shm/battery","r") as f:
                    cnt=f.read()
        try:
            z=cnt.split(";")
            if len(z)>2:
                val=float(z[1])
                #print(val)
                if val >=17: 
                    pic="4"                
                if val < 17: 
                    pic="3"
                if val < 16.8: 
                    pic="2"
                if val < 16: 
                    pic="1"
                cnt=pic+";"+str(round(val,2))+";"+ str(cut)+";"+ str(kurs)
                client_socket.send(cnt)
                #print("Socket send " + cnt)
                #client_socket.send("0;"+str(round(val,2))+";0")
        except:
            pass
        await asyncio.sleep(0.25)                   
   
def stop_drive():
    global ddir, DRIVE
    DRIVE=False
    with open("/run/shm/.PiMowBot_Motor.left","w") as File:
        File.write("0")
    with open("/run/shm/.PiMowBot_Motor.right","w") as File:
        File.write("0")
    ddir=0



def drive(cmd= '0'):
    """control the drive of PiMowBot."""
    global cmd_last, turtle, idle, ignition, ddir, drift, CUTTER, DRIVE
    #print("137 ",cmd)
    if cmd_last != cmd:
        left=0      # -100 bis 100
        right=0     # -100 bis 100
        if cmd == "0":
            with open("/run/shm/.PiMowBotIt.power","w") as File:  # wird im Ropilanmow nicht ausgewertet
                File.write("")
            ddir=0
            idle=time()
        elif 3 < len(cmd): # Joystick-Steuerung
            v=cmd.split(" ")
            if len(v)>2:
                return
            DRIVE=True        # wird gesetzt, damit bei abbrechendem Signal die Motoren gestoppt werden
            force=v[0]
            angel=v[1]
            
            #print("cmd ", cmd)
            #print("force ", force)
            #print("Angle ", angel)
            #print(cmd)
            if force=="cw":
                left=100 * min (1, float(angel))
                right=-left
            elif force=="cc":
                left=-100 * min (1, abs(float(angel)))
                right=-left
            else:
                force=float (force)
                angel=int (angel)
                if abs(angel) < 20:
                    if ddir < 0:
                        stop_drive()
                    left=100 * min (1, force)
                    right=left
                    ddir=1
                elif abs(angel) > 160:
                    if ddir > 0:
                        stop_drive() 
                    left=-100 * min (1, force)
                    right=left
                    ddir=-1
                elif (angel <= -20) and (angel >= -70):
                    if ddir==0:    
                        ddir=1
                    if ddir < 0:    # cw
                        left=100 * min (1, force)
                        right=-left
                    else: 
                        drift=1
                        right=100 * min (1, force)
                        left=(right - 10) - (right * abs (angel) / 110)
                elif (angel >= 20) and (angel <= 70):
                    if ddir==0:
                        ddir=1
                    if ddir<0:    # cc
                        left=-100 * min (1, force)
                        right=-left
                    else:
                        drift=1
                        left=100 * min (1, force)
                        right=(left - 10) - (left * angel / 110)
                elif (angel < -70) and (angel > -110):
                    if ddir==0:    # cc
                        left=-100 * min (1, force)
                        right=-left
                    elif drift > 0:
                        left=0
                        right=100 * min (1, force)
                    else:
                        left=0
                        right= -100 * min (1, force)
                elif (angel < 110) and (angel > 70):
                    if ddir==0:    # cw
                        left=100 * min (1, force)
                        right=-left
                    elif drift > 0:
                        left=100 * min (1, force)
                        right=0
                    else:
                        left=-100 * min (1, force)
                        right=0
                elif (angel <= -110) and (angel >= -160):
                    if ddir==0:
                        ddir=-1
                    if ddir>0:    # cc
                        left=-100 * min (1, force)
                        right = -left
                    else:
                        drift=-1
                        right=-100 * min (1, force)
                        left=right * (-90 + abs (angel)) / 90
                elif (angel >= 110) and (angel <= 160):
                    if ddir==0:    
                        ddir=-1
                    if ddir>0:    # cw
                        left=100 * min (1, force)
                        right=-left
                    else:
                        drift=-1
                        left=-100 * min (1, force)
                        right=right * (angel - 90) / 90
        elif cmd=="u":
            left=100
            right=100
        elif cmd=="d":
            left=-100
            right=-100
        elif cmd=="cw":
            left=100
            right=-100
        elif cmd=="cc":
            left=-100
            right=100
        elif cmd=="l":
            if cmd_last=="d":
                left=-100
                right=0
            else:
                left=0
                right=100
        elif cmd=="r":
            if cmd_last=="d":
                left=0
                right=-100
            else:
                left=100
                right=0
        elif cmd=="m":  # Toggle Mower Motor
            #print("myCutter on/ off")
            if CUTTER==True:
                CUTTER=False
            elif CUTTER==False:
                CUTTER=True
            #print("CUTTer==",CUTTER)    
            Cutter.toggle()       
            
        elif cmd=="sd": # Shutdown the Pi
            Cutter.on() # because to be compatible to PiMowBot, its LowActive t
            lg("System fährt runter")
            os.system("echo OFF > /dev/shm/shutdown")
            exitroutine()
        elif cmd=="tr":  # Turn right
            if  os.path.isfile("/run/shm/mowbrake"):    
                os.remove("/run/shm/mowbrake")
            with open("/run/shm/drivechain", "w")as f:
                f.write("cm_vor")        
        elif cmd=="Mo":
            lg("Dann Mow mal los cmd= "+ cmd)
            os.system("sudo systemctl start Mow_Std.service")
        elif cmd=="Ma":        
            lg("Stoppe Mowbetrieb cmd= " + cmd )
            os.system("sudo systemctl stop Mow_Std.service")
        elif cmd=="P1":        
            lg("Starte Programm "+ cmd )
            # to be definded
            
        elif cmd=="P2":        
            lg("Starte Programm "+ cmd)    
            # to be definded    
        
        elif cmd=="tl":  # Turn Left
            if  os.path.isfile("/run/shm/mowbrake"):    
                os.remove("/run/shm/mowbrake")
            with open("/run/shm/drivechain", "w")as f:
                f.write("cm_vor")    
            
        cmd_last=cmd
        
        left = round (turtle * min (100, max (-100, left)), 2)
        right = round (turtle * min (100, max (-100, right)), 2)
        
        # Motorwerte schreiben
        with open("/run/shm/.PiMowBot_Motor.left","w") as File:
            val = str(left)
            File.write(val)
        with open("/run/shm/.PiMowBot_Motor.right","w") as File:
            val = str(right)
            File.write(val)
    else:
        pass    


# MAC Address of the Android device (replace with your device's MAC address)

server_mac_address = "4E:09:46:00:00:CC"  # Replace with your Android's MAC address
_name="PiMowBotRC"
# UUID for SPP
UUID = "00001101-0000-1000-8000-00805F9B34FB"

def search_and_connect():
    global client_socket
    start=time()
    while True:
        if time()-start>0.8:
            BT_LED.toggle()
            start=time()
        # Search for the Android device using its MAC address
        print("Searching for Android server...")
        service_matches = bluetooth.find_service(address=server_mac_address, uuid=UUID)
        if len(service_matches) > 0:
            break
        sleep(1)
    
    if len(service_matches) == 0:
        print("Could not find any services matching the UUID.")
        return
    
    # Get the port number and name from the service match
    first_match = service_matches[0]
    port = first_match["port"]
    name = first_match["name"]
    host = first_match["host"]
    print(f"Connecting to \"{name}\" on {host} port {port}...")
    try:    
        # Create the client socket and connect to the server
        client_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        client_socket.connect((host, port))
        lg(strftime('%d-%b-%Y/%H:%M:%S')+ " Mit "+ name +" on "+ host+" port "+ str(port) + " verbunden")
        print("Connected to the Android server.")
    except:
        lg("Connecion ist fehlgeschlagen.")
        BT_LED.off()
        print("Connecion ist fehlgeschlagen.")

client_socket=None
lg("Starte BT-Scanner am: "+strftime('%d-%b-%Y/%H:%M:%S'))
piep.beep(0.2)
piep.nobeep(0.1)
piep.beep(0.1)
search_and_connect()
if client_socket:
    BT_LED.on()
    Rec = threading.Thread(target=receive)
    Rec.start()
else:
    search_and_connect 
async def main():
    tasks = []
    tasks = [
        asyncio.create_task(send_LifeData()),
        ]
    await asyncio.gather(*tasks)


try:
    while True:
        asyncio.run(main())

except KeyboardInterrupt:
   #client_socket.close()    
   print(strftime('%d-%b-%Y/%H:%M:%S')+" [  Bluetooth Remote interupted... ]")
   exitroutine()

finally:
   client_socket.close() 
   print("Programm beendet")
   
