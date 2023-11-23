# RoπLawnMow
![grafik](https://github.com/ullisun/RopiLawnMow/assets/86979044/6c603203-04eb-41f4-95ac-c69e949fea1a)


The RoπLawnMow Project is based on a Raspberry Pi. The intention is to replace e.g. defect electronic of an existing LawnMower
and use most of the components for further operation. A lot of information you will find in in the
https://www.diy-robot-lawn-mower.com/threads/roplawnmow.96/ Forum <br>
In order to achieve quick success, I use the PiMowBot IT SW http://pimowbot.tgd-consulting.de/ in this project. <br>
The SW can be obtained from TGD-Consulting http://www.tgd-consulting.de/Impressum.html.<br> In this first step I will control the brushless motors. To do this, the characteristics of the motors must be found. This can be done either with study of a data sheet or by using the MotorCal.py script. Are the motor parameters fixed, the first test drives can be done. For this I use the BLE Remote Control. The project is described here<br>https://github.com/TGD-Consulting/PiMowBot-RC<br>
In this phase of the project it makes sense to know how much voltage the battery has and how much current the motors needs. If you start the Ropi_INA3221.py Script,
you can see the result on the screen, or store the data for later anlysis. Also an file interface to the PiMowBotIT-SW is implemented The Ropi_INA3221.py is based on this example:
https://github.com/semaf/INA3221-Python-Library
Please copy the SDL_Pi_INA3221.py in the same direction or refer to the valid path

|  Outlook|
|-----------------------------------------------------------------|
|Implementation of gyroscope-based tracking control               |
|Implementation of additional interfaces to the PiMowBot IT SW  
|Creating a implementation concept  for a charger station |
|Generation of additional Ideas                                      |
