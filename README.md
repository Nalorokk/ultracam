##### Ultracam

Project goal is to do simple, easy to use service which monitors IP cameras using rtsp, looks for persons there using opencv, and notifies about them by Telegram.

###### Installation
~~~~
1) pip install opencv-python jinja2 sanic shapely python-telegram-bot
2) wget https://pjreddie.com/media/files/yolov3.weights -o cfg/yolov3.weights
3) edit config.json.example and save it as config.json. TG_TOKEN should be your telegram api bot token, TG_CHAT is chat id (might be chat room or user id) where to send messages. You might configure as many streams as you want.
4) python main.py
5) it's web would be available at 127.0.0.1:8000

![Screenshot](screenshot.jpg?raw=true "Telegram")