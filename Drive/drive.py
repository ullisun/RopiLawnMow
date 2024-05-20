# Update April 30th 2024 in order to fit with the PiMowBot Wiring.
# I changed rbt from 4 to 18 and
# pindir 11 to pindir 19
#
# Update 20th Mai
# Update Output Scection


from time import time, sleep, strftime
import signal
import sys, os
import pigpio
import read_RPM

class Motor:
    def __init__(self, PinPwm, PinDir, PinBreak, MaxSpeed, MainDir):
        self.PinPwm=PinPwm     
        self.PinDir=PinDir
        self.PinBreak=PinBreak
        self.MaxSpeed=MaxSpeed
        self.MainDir=MainDir
        pi.set_mode(self.PinDir, pigpio.OUTPUT)
        pi.set_mode(self.PinBreak, pigpio.OUTPUT)
        pi.write(self.PinBreak,0)
        pi.write(self.PinDir,0)
        
    def speed(self,value):
        pi.write(self.PinBreak,0)
        if value > self.MaxSpeed:
           value = self.MaxSpeed
        if value < self.MaxSpeed*-1:
           value = self.MaxSpeed*-1
        if value > 0:
             self.ffd()
        if value < 0:
             self.back()
        pi.set_PWM_dutycycle(self.PinPwm, abs(value))
    def stop(self):
        pi.write(self.PinBreak,1)
        pi.set_PWM_dutycycle(self.PinPwm, 0)

    def rel(self):
        pi.write(self.PinBreak,0)
    def ffd(self):
        if self.MainDir=="F":
            pi.write(self.PinDir,0)
        if self.MainDir=="B":
            pi.write(self.PinDir,1)
    def back(self):
        if self.MainDir=="F":
            pi.write(self.PinDir,1)
        if self.MainDir=="B":
            pi.write(self.PinDir,0)


class PID:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.last_error = 0
        self.integral = 0
        self.currentval=0

    def update(self, soll, ist , dt):
        error = soll - ist
        derivative = (error - self.last_error) / dt
        self.integral += error * dt
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        self.last_error = error
        
        #self.currentval += output * dt
        #output=(output+self.currentval)
        
        return output


# Callbacks for interrupt

def L_Hall(GPIO, level, tick):
   global l, UL, gl
   if last[lbtn] is not None:
      diff = pigpio.tickDiff(last[lbtn], tick)
      if level==1:
          l=l+1
          gl=gl+1
      if l>=ticksperRev:
         l=l-ticksperRev
         UL=UL+1
   last[lbtn] = tick

def R_Hall(GPIO, level, tick):
   global r, UR, gr
   if last[rbtn] is not None:
      diff = pigpio.tickDiff(last[rbtn], tick)
      if level==1:
        r=r+1
        gr=gr+1
      if r>=ticksperRev:
         r=r-ticksperRev
         UR=UR+1
   last[rbtn] = tick


def signal_term_handler(signal, frame):
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_term_handler)


PI=3.141592653589793
ticksperRev= 1054 
wheeldiameter=22   #cm

lbtn=17
rbtn=18
UR=0
UL=0
l=0
r=0
gl=0
gr=0
ogl=0
ogr=0
i=0
last = [None]*19
RPML=0
RPMR=0 

pi=pigpio.pi()

pi.set_mode(lbtn,pigpio.INPUT)
pi.set_mode(rbtn,pigpio.INPUT)

motorr=Motor(PinPwm=16,PinDir=21,PinBreak=20,MaxSpeed=245,MainDir="F")
motorl=Motor(PinPwm=13,PinDir=26,PinBreak=19,MaxSpeed=245,MainDir="B")

HallL=pi.callback(lbtn, pigpio.RISING_EDGE, L_Hall)
RPML = read_RPM.reader(pi, lbtn,pulses_per_rev=ticksperRev,min_RPM=0.0)
HallR=pi.callback(rbtn, pigpio.RISING_EDGE, R_Hall)
RPMR = read_RPM.reader(pi, rbtn,pulses_per_rev=ticksperRev,min_RPM=0.0)
motorl.stop()
motorr.stop()
start= time()
tripPath=os.path.abspath(".")+"/trips/"

def drive(rpml,rpmr,ziell,zielr):
    global gl, gr
    gr=0
    gl=0
    valuer=1
    valuel=1 
    dirr=1
    dirl=1
    ovaluel=0
    ovaluer=0
    # 890 = halbe Umdrehung 
    pidl = PID(Kp=1.2, Ki=0.1, Kd=0.9)
    pidr = PID(Kp=1.2, Ki=0.1, Kd=0.9)
    dt = 0.1
    current_valueL = 0.0
    current_valueR = 0.0
    if abs(rpml)==0:
        ziell=0
    if rpml<0:
        dirl=-1
    if abs(rpmr)==0:
        zielr=0    
    if rpmr<0:
        dirr=-1
    sollRPML=abs(rpml)
    sollRPMR=abs(rpmr)
    cancel=False
    done=True
    
    print ("Zeit;  Soll L; Value L; RPM-L ;Soll R ; Value R; RMP R  ;    Ticsl       ;  Ticsr ")
    print ("==================================================================================")  
          
    while valuer>0 or valuel>0 and cancel == False:  # time()-start < 30:
        sleep(dt)
        if gr> zielr -(zielr / 4) and sollRPMR > 10: #ticksperRev*setRev-ticksperRev/4 and sollRPM> 10:
            sollRPMR= int(sollRPMR-3)
        if gl> ziell -(ziell/ 4) and sollRPML > 10: #ticksperRev*setRev-ticksperRev/4 and sollRPM> 10:
            sollRPML= int(sollRPML-3)
        links= int(RPML.RPM())
        rechts= int(RPMR.RPM())
        control_signalL = pidl.update(sollRPML,links,  dt)
        current_valueL += control_signalL * dt
        control_signalR = pidr.update(sollRPMR,rechts, dt)
        current_valueR += control_signalR * dt
        
        if gr >= zielr: #880/2: #setRev * ticksperRev:
            valuer=0
            ovaluer=0
            motorr.stop()
            #print(gr, " ", zielr, " Rechter Motor Stop")
        else:
            valuer=(valuer+current_valueR)
           
        
        if gl >= ziell: #880/2: #setRev * ticksperRev:
            valuel=0
            ovaluel=0
            motorl.stop()
            #print(gl, " ", ziell, " Linker Motor Stop")
        else:            
            valuel=(valuel+current_valueL)
        print ((str((round(time()-start,2)))+"\t;"+ str(sollRPML) + "\t;"+str(round(valuel/245*100,0)) + "\t;" 
              +str(links) +"\t;"+str(sollRPMR) +"\t;"+str(round(valuer/245*100,0))+ "\t;"+ str(rechts)+ "\t; Ticsl ;"+str(gl) + "\t; Ticsr ;" +str(gr)).expandtabs(8))
        #print (f"{'Zeit:' + round(time()-start,2):<25}'SollRPM {sollRPML}")        #, "\t;", round(valuel/245*100,0), "\t;" ,links,"\t;", sollRPMR, "\t;",round(valuer/245*100,0), "\t;", rechts, "\t; Ticsl ;", gl, "\t; Ticsr ;", gr)  
        try:
            if valuel != ovaluel:
                motorl.speed(int(valuel*dirl))    
                #pi.set_PWM_dutycycle(mlpwm, int(valuel))
                ovaluel=valuel
            if valuer != ovaluer:
                motorr.speed(int(valuer*dirr))
                #pi.set_PWM_dutycycle(mrpwm, int(valuer))
                ovaluer=valuer
        except:
            print(valuel, "  ",valuer)
            done=False
            cancel=True
    return done       

def goahead(rpm,distance):
    tics = int((distance / (wheeldiameter * PI)) * ticksperRev)
    print("zu erwartende Tics: ", tics)
    print("============================\n")
    try:
        drive(int(rpm),int(rpm),tics,tics)
    except KeyboardInterrupt:
        print("[ MotorControl Management: Brushless MotorControl interupted... ]")
 

def dofile(path, file):        
    try:
         
       with open(path+file,"r") as f:      #with open("/home/pi/RopiLawnMow/trips/cw_change","r") as f:    
           m=[_.rstrip('\n') for _ in f]
       for zeile in m:
            print(zeile)
            if zeile.count(",")==3 and zeile.startswith("#")==False:
                data=zeile.split(",")
                erg=drive(int(data[0]),int(data[1]),int(data[2]),int(data[3]))  #erg=drive(-12,12,300,300) für zurück mit 12 RPML, vor mit 12 RPMR, jewils mit 300 tics
                if erg== False:
                    raise "Fehler"
            elif zeile.count(",")== 0 and zeile.startswith("#")==False:
                print("Fertig")                
            else:
                if zeile.startswith("#"):
                    print(zeile)
                else:
                    print("Fehler in : ", zeile)

    except OSError:
        print("[ MotorControl Management: Brushless MotorControl interupted Tripfile not found or not specified ]")        
    except KeyboardInterrupt:
        print("[ MotorControl Management: Brushless MotorControl interupted... ]")
    

if __name__ =="__main__":
    Fehler=False
    file=""
    if len(sys.argv)<2:
        print("Es wurde keine Datei angegeben")
        Fehler = True
        print("Fehler ", Fehler)
        
    if Fehler == False:
        
        if len(sys.argv)==3 and abs(int(sys.argv[1])) >= 8 and abs(int(sys.argv[1])) <= 26:
            print("Vorgabe Argu. 1: ", int(sys.argv[1]), " , Vorgabe Argu. 2: ", int(sys.argv[2]))
            print("")
            goahead(int(sys.argv[1]),int(sys.argv[2]))
        else:           
            file=sys.argv[1]
            if os.path.exists(tripPath+file)==False:        
                print(sys.argv[1] +" wurde nicht gefunden")
                Fehler=True   
            else:
                dofile(tripPath,file)    
        
    
    
    print("[ MotorControl Management: Brushless MotorControl finished !!! ]")
    motorl.stop()
    motorr.stop()
    motorl.rel()
    motorr.rel()
    HallL.cancel()
    HallR.cancel()
    RPML.cancel()
    RPMR.cancel()
    pi.stop() 
                        
      

