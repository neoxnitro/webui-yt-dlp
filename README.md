[params]
extraHead = '<meta name="google-site-verification" content="8sSXS-rETrfpLP1KjWjA1iLssLwKqxvjygdSD3vzrIY" />'

# webui-yt-dlp
Light web ui for yt-dlp, backhand written in python (Flask and SocketIO)

<img src="https://github.com/neoxnitro/webui-yt-dlp/blob/main/Capture.PNG">

### Platform
- Linux (tested on Debian Buster release)
- Windows 10

### Features
- Support video convertion into multiple audio format (mp3, flac, wav, mp4a, aac)
- Possibility to retrive of all supported formats and select a specific one (Video & Audio, Video only, Audio only, with various caracteristics)
- Parallel download request is supported

### Requirement
- Python 3.7
- yt-dlp <https://github.com/yt-dlp/yt-dlp>
- ffmpeg (optional, if you want extract audio function)
- waitress-serve (optional, if you want make the main Python script as a linux service)

### Parameters

You have the possibility to easily change the parameters directly by editing main Python script **webui-yt-dlp.py**

```python
   # global parameters
   DOWNLOAD_DIR = "download"
   LINUX_FFMPEG_PATH = "/usr/bin/ffmpeg"
   WINDOWS_FFMPEG_PATH = "C:\\Users\\Utilisateur\\Downloads\\bin\\ffmpeg.exe"
   HTTP_PORT = 5005
```

N.B if you will use waitress-serve, the server port is also present into the file **webui-yt-dlp.service**

### Installation (linux)(manual launch)
- git clone git@github.com:neoxnitro/webui-yt-dlp.git
- cd webui-yt-dlp
- pip3 install -r requirements.txt
- python3 webui_yt_dlp.py

```php
root@root:~/webui-yt-dlp$ python3.7 webui-yt-dlp.py 
WebSocket transport not available. Install simple-websocket for improved performance.
 * Serving Flask app "webui-yt-dlp" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://0.0.0.0:5005/ (Press CTRL+C to quit)
```

### Installation as a Linux service (Python waitress-serve is required !)
- cd webui-yt-dlp
- sudo cp webui-yt-dlp.service /etc/systemd/system/
- sudo systemctl enable webui-yt-dlp.service
- sudo systemctl daemon-reload
- sudo systemctl start webui-yt-dlp.service
- sudo systemctl status webui-yt-dlp.service

```php
root@root:~/webui-yt-dlp$ sudo systemctl status webui-yt-dlp.service 
● webui-yt-dlp.service - Youtube web UI app service
   Loaded: loaded (/etc/systemd/system/webui-yt-dlp.service; enabled; vendor preset: enabled)
   Active: active (running) since Wed 2022-06-22 14:55:52 CEST; 20h ago
 Main PID: 14325 (waitress-serve)
    Tasks: 2 (limit: 2127)
   Memory: 37.1M
   CGroup: /system.slice/webui-yt-dlp.service
           └─14325 /usr/bin/python3 /home/root/.local/bin/waitress-serve --listen=0.0.0.0:5005 --call webui_yt_dlp:create_app
```
