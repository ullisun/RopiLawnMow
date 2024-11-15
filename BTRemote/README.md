![grafik](https://github.com/user-attachments/assets/9b70d9d1-bb97-4374-85b8-d3fc186df280)

### Here you will find the files of RoπLawnMows Remote Control
![grafik](https://github.com/user-attachments/assets/ac51a8ec-d32c-4444-866c-bd615d00e137)

The Python file runs on the Raspberry Pi as a service in /etc/systemd/system/ 
The advantage: The service starts the Python Script every time agian if the connection breaks down
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

I coded the Android App in Android Studio. I am not not an expert in Android Studio, so I exported the Project as
zip file and also as apk. So far I tested it you can copy the apk file in your Android Download directory.
A double click will install the App. In the zip file all sources are included if you want to adapt it to your needs.

When I started with coding, my plan was to have a BLE Communication between Pi and mobile Phone. This was extremly 
difficult for me. So I changed it to the calssic Bluettooth stack. But I forgot to change the name of the App.
So if you will test it, use classic BT and pair your mobile before with your Pi.
-Good Luck- 

Your Feedback is welcome
