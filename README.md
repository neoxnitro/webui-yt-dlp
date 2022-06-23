# webui-yt-dlp

Light web ui for yt-dlp, backhand written in python (Flask and SocketIO)

<img src="https://github.com/neoxnitro/webui-yt-dlp/blob/main/Capture.PNG">

### Platform
- Linux (tested on Debian Buster release)
- Windows 10

### Features
- Support video convertion into multiple audio format (MP3, FLAC, WAV, MP4a, aac)
- Retrive of all supported formats and possibility to select a specific format (Video & Audio, Video only, Audio only)
- Parallel download request is supported


### Requirement
- Python 3.7
- ffmpeg (optional, if you want extract audio function)
- waitress-serve (optional, if you want make the main Python script as a linux service)

### Installation (linux)
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
