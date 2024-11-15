RoπLawnMows Remote Control

Here you will find the files of RoπLawnMows Remote Control


![grafik](https://github.com/user-attachments/assets/ac51a8ec-d32c-4444-866c-bd615d00e137)

The Python file runs on the Raspberry Pi and runs as a service.
The advantage: The Service starts the Python Script every time agian if the connection is lost
```
[Unit]
Description=BT-remoteClassic
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/home/pi/Mower/bin
ExecStart= /usr/bin/python /home/pi/Mower/bin/BT_remote.py
User=pi
Restart=always
RestartSec=2
SyslogIdentifier=BT-Classic

[Install]
WantedBy=multi-user.target
```

I coded the Android App in Android Studio. I am not familiar with Android Studio, so I exported the Project as
zip File and also as apk. So far I tested it you can copy the ap file in your Android Download Directory.
A double Click will install the App. 

When I started the Coding, my plan was to have a BLE Communication between Pi and mobile Phone. This was extremly 
difficult for me, so I changed ist to the calssic Bluettooth stack. But I forgot to change the name of the App.
So if you will test it, use classic BT and pair your mobile before with your pi.
Good Luck- 
Your Feedback is welcome
