## Motor Calibration

### To run this script please type sudo pigpiod

First function you should call is the turnweel function. For this comment out all other functions in line 311, 312 and 313.
if you start trunwheel, every wheel has to turned by hand. The tics per wheel are displayed on the screen. This allows you to determine the exact HALL pulses per revolution. You have to assign this value to the  variable ticksperRev= in line 115. <br><br>
![grafik](https://github.com/ullisun/RopiLawnMow/assets/86979044/642c0e50-9b17-4d48-a9bc-0d895225c16c)
<br>
After that you can check it with the **Mon_RPM()** function.<br>
Disable turnwheel and enable the function MonRPM in line 311. The wheels will turn around for 30 sec. During this time the screen displays the counted "tics", "revolutions" and "rpm" of each wheel.

<br><br>
![grafik](https://github.com/ullisun/RopiLawnMow/assets/86979044/5ad2c6bc-6241-4cd7-ab09-ee7f9e1eab19)
<br>
Now you can run the **hallcheck()** function<br>
Disable Mon_RPM and enable the function halcheck in line 312. The wheels wirl turarround 12times. And stop at nearly the same position where they started before.
If not you have to check the value of ticksperRev and ajust it by 1 or -1 .<br><br>
Last you can run the **testsoll()** function.<br>
Disable hallcheck and enable the function testsoll in line 313.
This function will use a PID Controller to drive the wheels with a constant rpm. So far I know you have to adjust the PID parameters depending of your motor characteristicas.
In my Ro**π**LawnMow are Motors from Dunker. Could be that LINIX brushless Motors needs differend PID parameters. You have to try and play with this.
Howewer at the end the wheels will turn 5 times with an rpm of 20 and stop at the same positon as they started nearly at the same time. This is the different between the hallcheck
function. You can export your screen to Excel and create a diagramm which helps you to tune your PID Controller like this or better.<br>
![grafik](https://github.com/ullisun/RopiLawnMow/assets/86979044/cdf76c98-1eaa-4515-9197-c783bc9881fe)
<br>
### Good Luck





