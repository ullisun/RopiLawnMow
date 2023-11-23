from time import time, sleep, strftime
import signal
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
        pi.set_PWM_dutycycle(self.PinPwm, 0)
        pi.write(self.PinBreak,1)
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

    def update(self, error, dt):
        derivative = (error - self.last_error) / dt
        self.integral += error * dt
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        self.last_error = error
        return output

''' 
            !!!!!!!! Zuvor muss der Befehl sudo pigpiod ausgeführt werden  !!!!!!!!
            =======================================================================           
       
            Als erstes sollte Turnweel ausgeführt werden. die Aufrufe mon_RPM und hallcheck sind dann auszukommentieren         
            Bei trunwheel wird jedes Rad von Hand gedreht. Auf dem Bildschirm werden die Tics pro Rad angezeigt. Damit lassen sich
            ziehmlich exact die HALL Impulse pro Umdreung ermitteln, die dann als Wert der Variablen ticksperRev= xxxx in Zeile 115 
            eingetragen wird.  
       
            Danach sollte turnwheel auskommentiert werden und die funktion mon_RPM aktiviert werden.
            Diese Funktion startet beide Motoren auf Geschwindigkeit und wertet die Tics und RPMS aus. Die Motore werden 30 Sekunden
            laufen und am Ende werden die gezählten Tics und gemessene RPMs ausgegeben.
            
            Als drittes kann die hallcheck Funktion durchgeführt werden. Dazu ist es ratsam eine Markierung auf den Rädern anzubringen.
            Die Funktion lässt die Motoren beschleunigen und nach ererechen der max drehzahl werden die Motoren wieder langsamer.
            Nach 12 Umdrehungen werden die Motoren stoppen. Die Markierung der Räder sollte dann wieder an der Startposition stehen.
            Sind die Abweichungen größer als ca. 5mm muss ggf ein neuer ticksperRev Wert eingestellt werden.

           Inspiriert durch:
           https://raspberrypi.stackexchange.com/questions/62339/measure-rpm-using-hall-sensor-and-pigpio
'''

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

lbtn=17
rbtn=4
ticksperRev=1093   #597
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

motorl=Motor(PinPwm=16,PinDir=20,PinBreak=21,MaxSpeed=176,MainDir="F")
motorr=Motor(PinPwm=13,PinDir=11,PinBreak=26,MaxSpeed=176,MainDir="B")

HallL=pi.callback(lbtn, pigpio.RISING_EDGE, L_Hall)
RPML = read_RPM.reader(pi, lbtn,pulses_per_rev=ticksperRev,min_RPM=0.0)
HallR=pi.callback(rbtn, pigpio.RISING_EDGE, R_Hall)
RPMR = read_RPM.reader(pi, rbtn,pulses_per_rev=ticksperRev,min_RPM=0.0)

motorl.stop()
motorr.stop()

start= time()

def turnwheel():
    global ogr,ogl
    start=time()    
    while time()-start <=60:
        if ogr!=gr or ogl != gl:
            print("Links: " ,gl, " Rechts ",gr)
            ogr=gr
            ogl=gl
        sleep(0.01)    
    print("Schluss nach,", time()-start, " Sekunden")
    print("Ende") 


def mon_RPM():
    output=start
    motorl.ffd()
    motorr.ffd()
    motorl.speed(100)
    motorr.speed(100)    
    while time()-start <=20:
        if time()-output >=1:
            print("Verbleiben= ", round(30-(time()-start),1), "Sekunden:  Links: Tics=",gl, " Anzahl der Umdrehungen=", UL, " RPM= ",round(RPML.RPM(),2), " Rechts: Tics= ",gr, " Anzahl der Umdrehungen=", UR, " RPM= ",round(RPMR.RPM(),2))         
            output=time()
        #if time()-start> 10:
        #    motorr.stop()    
            
    motorr.stop()    
    motorl.stop()    

    print("Tics Links=",gl, " Anzahl der Umdrehungen=", UL, " RPM= ",round(RPML.RPM(),2), " Tics Rechts= ",gr, " Anzahl der Umdrehungen=", UR, " RPM= ",round(RPMR.RPM(),2))         
    print("Programm Ende nach,", time()-start, " Sekunden") 


def hallcheck():
    i=0
    valuel=0
    valuer=0
    start= time()
    motorr.stop()
    motorl.stop()
    while i<=176:
        valuel=i
        valuer=i
        motorr.speed(valuer)
        motorl.speed(valuel)
        sleep(0.050)
        i=i+1
        print("Links: Tics=",l, " Anzahl der Umdrehungen=", UL, " RPM= ",round(RPML.RPM(),2), " Rechts: Tics= ",r, " Anzahl der Umdrehungen=", UR, " RPM= ",round(RPMR.RPM(),2))         
    print("Maximal Speed erreicht")    
    sleep(5)
    while True:
        motorr.speed(valuer)
        motorl.speed(valuel)
        sleep(0.050)
        if i>=64:        
            i=i-1
            valuel-=1 
            valuer-=1
        #print(i)
        print("Links: Tics=",l, " Anzahl der Umdrehungen=", UL, " RPM= ",round(RPML.RPM(),2), " Rechts: Tics= ",r, " Anzahl der Umdrehungen=", UR, " RPM= ",round(RPMR.RPM(),2))         
        if gr> ticksperRev*12-ticksperRev/4 and valuer > 34:
            #print("BremseR ", gr," ", ticksperRev*12-ticksperRev/4, " ", i )
            valuer=32
        if gl> ticksperRev*12-ticksperRev/4 and valuel > 34:
            #print("BremseL")
            valuel=32
        if gr>=ticksperRev*12:
            print("rechten Muss motor Stoppen")
            valuer=0
            motorr.stop()
        if gl>=ticksperRev*12:
            valuel=0
            motorl.stop()
        if gr>= ticksperRev*12 and gl >= ticksperRev*12:
            break    
    
    print("Schluss nach,", round(time()-start,2), " Sekunden")
    print("Ende")


def testsoll():
    start=time()
    ir=1          #=> ca. 14 prm auf dem Teststand bi 20 Volt Akkuspannung
    #ir=80          #=> ca. 22 prm auf dem Teststand bi 20 Volt Akkuspannung
    #ir=110         #=> ca.31 prm auf dem Teststand bi 20 Volt Akkuspannung
    #ir= 130        #=> ca.36 prm auf dem Teststand bi 20 Volt Akkuspannung 29 bei 17Volt Akku-Spannung
    il=ir
    oil=il
    oir=ir
    setRev=5
    pidl = PID(Kp=0.8, Ki=0.1, Kd=0.9)
    pidr = PID(Kp=0.8, Ki=0.1, Kd=0.9)
    dt = 0.1
    current_valueL = 0.0
    current_valueR = 0.0
    motorl.ffd()
    motorr.ffd()
    #pi.write(mrbreak,0)
    #pi.write(mlbreak,0)
    #pi.write(mldir,1)
    #pi.write(mrdir,0)
    motorr.speed(ir)
    motorr.speed(il)
    #pi.set_PWM_dutycycle(mrpwm, ir)
    #pi.set_PWM_dutycycle(mlpwm, il)
    sollRPM=20
    print("los Jetzt")
    while ir>0 or il>0:  # time()-start < 30:
        sleep(0.05)
        #if ir > 80 and gr > ticksperRev*setRev / 2:
        #    sollRPM= 20 
                    
        
        if gr> ticksperRev*setRev-ticksperRev/4 and sollRPM> 15:
            sollRPM= int(sollRPM/2)
             
        links= int(RPML.RPM())
        rechts= int(RPMR.RPM())
        errorL=sollRPM - links #rechts-links
        control_signalL = pidl.update(errorL, dt)
        current_valueL += control_signalL * dt
        errorR=sollRPM-rechts        
        control_signalR = pidr.update(errorR, dt)
        current_valueR += control_signalR * dt
        #if abs(error) >= 1:
        if gr >= setRev * ticksperRev:
            ir=0
        else:
            ir=(ir+current_valueR)
        if gl >= setRev * ticksperRev:
            il=0
        else:            
            il=(il+current_valueL)
    
        #print (round(current_valueL,0), " rpm Links ", links, " dutyCycle Links=", round(il,0),"  rpm Rechts ", rechts, " ir= ", round(ir,0) , " Ticsl ", gl, " Ticsr ", gr)
        #print ("sollRPM=", sollRPM, " rpm Links ", links, " dutyCycle Links=", round(il,0),"  rpm Rechts ", rechts, " dutyCycle Rechts= ", round(ir,0) , " Ticsl ", gl, " Ticsr ", gr)
        print (round(time()-start,2),";", sollRPM, ";", round(il/176*100,0), ";" ,links,";", round(ir/176*100,0), ";", rechts, "; Ticsl ;", gl, "; Ticsr ;", gr)  
        #    print("il0= ", il)
                        
        #if il >= 176:
        #    il=176
        #if ir >= 176:
        #    ir=176
        try:
            if il != oil:
                motorl.speed(int(il))    
                #pi.set_PWM_dutycycle(mlpwm, int(il))
                ol=il
            if ir != oir:
                motorr.speed(int(ir))
                #pi.set_PWM_dutycycle(mrpwm, int(ir))
                oir=ir
        except:
            print(il, "  ",ir)

        
if __name__ =="__main__":
    
    try:
             
       turnwheel()
       # mon_RPM()       
       #hallcheck()
       #testsoll()

    except KeyboardInterrupt:
        
        print("[ MotorControl Management: Brushless MotorControl interupted... ]")
    
    finally:
        print("[ MotorControl Management: Brushless MotorControl finished !!! ]")
        motorl.stop()
        motorr.stop()
        HallL.cancel()
        HallR.cancel()
        RPML.cancel()
        RPMR.cancel()
        pi.stop()    

