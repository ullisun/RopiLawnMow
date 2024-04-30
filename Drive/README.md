## Drive

### To run the drive.py script please type sudo pigpiod when your pi is up and running 

You should copy the whole Drive Folder to your Pi. Your Filesystem should look like this
<br><br>
![grafik](https://github.com/ullisun/RopiLawnMow/assets/86979044/564280cd-e4f9-4861-a247-3ff045729c20)
<br>
When you finished your MotorCalibration as described in the README.md of the MotorCal folder, you can run the drive.py
Please have a look into the trips folder and open e.g. the ccw180 file. <br>
There is only one line **-8,8,880,880** <br>
The syntax is: Left wheel turns with 8 rpm backwards, right wheel turns with 8 rpm forward, and both engines stopps after 880 tics (hall impulses) <br>
You can start this action with **python drive.py ccw180**
In my configuration it is a exact 180 degrees turn.
So feel free to change the values.

There is an other option<br>
If you run **python drive.py 12 300** <br>Your mower will run forward with 12 rpm (both wheels) and will stop after 300 cm. <br>
the exact **ticksperRev=1093** and **wheeldiameter=22** in line 109 / 110 of your mower is required.
The rpms you type in as parameter should be greater than 7 and less the 27. If you use negative rpm the mower drives  backward<br>
Please have in mind that this project is in development and other features I will implement as soon as I find the time. <br>
<br>
Have fun - Your feedback is welcome








