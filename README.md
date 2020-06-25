##### Ultracam

Project goal is to do simple, easy to use service which monitors IP cameras using rtsp, looks for persons there using opencv, and notifies about them by Telegram.

###### Installation
~~~~
1) pip install opencv-python jinja2 sanic shapely python-telegram-bot
2) wget https://pjreddie.com/media/files/yolov3.weights -o cfg/yolov3.weights
3) python main.py
4) it's web would be available at 127.0.0.1:8000, it is possible to configure rtsp streams there
~~~~
![Screenshot](screenshot.jpg?raw=true "Telegram")

##### SystemD .unit
It is usermode systemd unit, should be run with --user and placed in ~/.config/systemd/user/ultracam.service
~~~~
[Unit]
Description=Ultracam Server

[Service]
Type=simple
WorkingDirectory=/home/USER/ultracam
ExecStart=python main.py
Restart=on-failure
RestartSec=10
KillMode=process

[Install]
WantedBy=default.target

~~~~