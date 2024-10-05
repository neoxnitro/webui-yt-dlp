import getopt
import json
import os
import re
import subprocess
import sys
import threading
import time
from os import read, path

from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO



# Disable print
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore print
def enablePrint():
    sys.stdout = sys.__stdout__

# global variable
DOWNLOAD_DIR = "download"
FFMPEG_PATH = "/usr/bin/ffmpeg"
LINUX_FFMPEG_PATH = "/usr/bin/ffmpeg"
WINDOWS_FFMPEG_PATH = "C:\\Users\\Utilisateur\\Downloads\\bin\\ffmpeg.exe"
HTTP_PORT = 5005

super_dl_id = 999999999
thread_running = {}

class Object(object):
    pass


# function will be called by waitress-serve
def create_app():

    global FFMPEG_PATH


    argv = ""
    disable_print = ''
    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["disabe_print="])
    except getopt.GetoptError:
        print('script.py -disabe_print <true/false>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('test.py -disabe_print <true/false>')
            sys.exit()
        elif opt in ("-disabe_print", "--disabe_print"):
            disable_print = distutils.util.strtobool(arg.lower().capitalize())

    if disable_print:
        print("print is disabled")
        blockPrint()

    enablePrint()
    print("O.S Name:", os.name, file=sys.stderr)

    if os.name == "posix":
        FFMPEG_PATH = LINUX_FFMPEG_PATH
        socketio.run(app, host="0.0.0.0", port=HTTP_PORT)

    if os.name == "nt":
        FFMPEG_PATH = WINDOWS_FFMPEG_PATH
        socketio.run(app)

app = Flask(__name__)
app.config['SECRET_KEY'] = '+MbQeThVmYq3ggw9z$H&F)J@NcRfUjXnZr4u7x!A%D*G-KaPfSgVkYp3s5v8y/B?'

# index (main page)
@app.route('/')
def index():
    return render_template('youtube-web-ui.html')

# download files link
@app.route('/' + DOWNLOAD_DIR +'/<path:filename>', methods=['GET', 'POST'])
def download(filename, os=None):
    print(download.__name__, "file from host to client:[" + filename + "]")
    donwload_location = app.root_path
    l_donwload_location = path.join(donwload_location, DOWNLOAD_DIR)
    print(download.__name__, "path: " + l_donwload_location)
    return send_from_directory(directory=l_donwload_location, path=filename)

# html icon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# socket (for inter process communication between the python thread and client HTML page)
socketio = SocketIO(app, async_mode='threading')

# download video request from client
@socketio.on('download_video')
def handle_json(xjson):
    global super_dl_id
    global thread_running

    print('received json: ' + str(xjson))
    sid = request.sid
    job_thread = socketio.start_background_task(fct_download_video, sid, xjson, super_dl_id)
    thread_running[job_thread.ident] = True
    # decrement the thread dl_id (result, a download reverted list (first = new one))
    super_dl_id -= 1
    return 'one', 2

# get video formats request from client
@socketio.on('getFormat')
def handle_getformat(xjson):
    print(handle_getformat.__name__, 'received')
    sid = request.sid
    fct_get_video_formats(sid, xjson)

# stop process request from client
@socketio.on('stop_thread')
def handle_stop_thread(xjson):
    global thread_running
    print(handle_stop_thread.__name__, 'received')

    arg_dict = json.loads(xjson)
    thread_running[int(arg_dict['thread_id'])] = False

# thread function "get video formats" (asynchronous communication)
def fct_get_video_formats(sid, xjson):
    arg_dict = json.loads(xjson)
    l_formats_dico = {}

    socketio.emit('video_formats', "processing", to=sid)

    youtube_dl_popen = ['yt-dlp']

    # currently "list" is not supported yet
    if "&list=" in arg_dict['video']:
        arg_dict['video'] = re.split("&list=", arg_dict['video'])[0]

    if arg_dict['video'] != "":
        youtube_dl_popen.append('-F')
        youtube_dl_popen.append(arg_dict['video'])

    process = subprocess.Popen(youtube_dl_popen, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    process_out = ""
    process_out_raw = ""

    while (True):

        # retrieves strings output
        try:
            # read and decode string
            process_out_raw = read(process.stdout.fileno(), 512).decode('ISO-8859-1', 'ignore')

        except OSError:
            # the os throws an exception if there is no data
            print(fct_get_video_formats.__name__, '[No more data]')
            socketio.emit('video_formats', "error", to=sid)
            return

        # remove if string is too small (end of process)
        if len(process_out_raw) < 10:
            process_out_raw = ""

        process_out += process_out_raw.rstrip()
        #print("process_out: " + process_out)

        # split string into lines
        process_out_list = process_out.split('\n')

        l_before_formats_dico_len = len(l_formats_dico)
        for line in process_out_list:
            match = re.split('(\d+)', line)
            if line[0].isnumeric() and len(match) > 3 and match[1].isnumeric():
                #print(match[1])
                code = match[1]
                text = line[len(match[1]):].strip()
                text = text.split(",", 1)[0]
                l_formats_dico[code] = text

        if len(l_formats_dico) > l_before_formats_dico_len:
            socketio.emit('video_formats', l_formats_dico, to=sid)

        elif len(l_formats_dico) == l_before_formats_dico_len \
                and l_before_formats_dico_len == 0:
            #print(fct_get_video_formats.__name__, "looking for an error")
            for line in process_out_list:
                if "error" in line.lower() or "warning" in line.lower():
                    print(fct_get_video_formats.__name__, "error: " + line)
                    l_formats_dico[-1] = line
                    socketio.emit('video_formats', l_formats_dico, to=sid)
                    return

        if not process_out_raw:
            print(fct_get_video_formats.__name__, '[No more data]')
            return

# thread function "download video + convert to audio" (asynchronous communication)
def fct_download_video(sid, xjson, dl_id):
    global thread_running
    var = 0
    thread_id = threading.get_ident()

    arg_dict = json.loads(xjson)
    data = '{ \
                "dl_id" : 0, \
                "thread_id" : 0, \
                "step": "Processing", \
                "progress": 0, \
                "link": "no-set", \
                "title": "no-set", \
                "artist": "no-set", \
                "output_filename": "no-set", \
                "action": "none"\
            }'

    data_dict = json.loads(data)
    data_dict['dl_id'] = dl_id
    data_dict['progress'] = 'Process ...'
    data_dict['step'] = 'Thread created'
    data_dict['action'] = 'none'
    data_dict['format'] = ''
    data_dict['format_desc'] = ''
    socketio.send(data_dict, json=True, to=sid)

    print(fct_download_video.__name__, 'Thread creation [Download]: ' + str(json))

    youtube_dl_popen = ['yt-dlp']

    # currently "list" is not supported yet
    if "&list=" in arg_dict['video']:
        arg_dict['video'] = re.split("&list=", arg_dict['video'])[0]

    if arg_dict['video'] != "":
        youtube_dl_popen.append(arg_dict['video'])

    # download path
    youtube_dl_popen.append("--paths")
    youtube_dl_popen.append(DOWNLOAD_DIR)

    # if the format is "defaut" (0) is hidden
    if arg_dict['format'] != "0":
        youtube_dl_popen.append('-f ' + arg_dict['format'])

    # "best", "aac", "flac", "mp3", "m4a", "opus", "vorbis", or "wav"

    if arg_dict['extract_audio']:
        youtube_dl_popen.append("--extract-audio")
        youtube_dl_popen.append("--ffmpeg-location")
        youtube_dl_popen.append(FFMPEG_PATH)
        youtube_dl_popen.append("--format")
        youtube_dl_popen.append("bestaudio")
        youtube_dl_popen.append("--audio-format")
        if arg_dict['audio_format'] == "check_convert_into_mp3":
            youtube_dl_popen.append("mp3")
        elif arg_dict['audio_format'] == "check_convert_into_aac":
            youtube_dl_popen.append("aac")
        elif arg_dict['audio_format'] == "check_convert_into_m4a":
            youtube_dl_popen.append("m4a")
        elif arg_dict['audio_format'] == "check_convert_into_flac":
            youtube_dl_popen.append("flac")
        elif arg_dict['audio_format'] == "check_convert_into_wav":
            youtube_dl_popen.append("wav")

    # remove exotic characters
    youtube_dl_popen.append("--restrict-filenames")

    print(fct_download_video.__name__, 'youtube_dl_popen:' + str(youtube_dl_popen))
    process = subprocess.Popen(youtube_dl_popen, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    last_sent_process_out = ""

    # build json data
    data_dict = json.loads(data)
    data_dict['dl_id'] = dl_id
    data_dict['progress'] = ""
    data_dict['thread_id'] = str(thread_id)
    if arg_dict['format'] != "0":
        data_dict['format'] = arg_dict['format']
        data_dict['format_desc'] = arg_dict['format_desc']
    else:
        data_dict['format'] = ''
        data_dict['format_desc'] = ''
    data_dict['link'] = arg_dict['video']
    data_dict['action'] = 'stop'

    proccessing = 0
    while (True):
        proccessing += 1

        if proccessing == 4:
            proccessing = 1

        start = time.time()
        # retrieves strings output
        try:
            # read and decode string
            process_out_raw = read(process.stdout.fileno(), 512).decode('ISO-8859-1', 'ignore')

        except OSError as error:
            # the os throws an exception if there is no data
            print(fct_download_video.__name__, 'OSError:' + error)
            data_dict['progress'] = 'OSError' + error
            data_dict['step'] = 'Error'
            data_dict['action'] = 'none'
            data_dict['format'] = ''
            data_dict['format_desc'] = ''
            socketio.send(data_dict, json=True, to=sid)
            return
        end = time.time()
        print(fct_download_video.__name__, "Elapsed exec time: " + str(end - start))

        # remove if string is too small (end of process)
        if len(process_out_raw) < 10:
            process_out_raw = ""

        process_out = process_out_raw.rstrip()
        print(fct_download_video.__name__, "process_out: [" + process_out + "]")

        # thread still allowed to run ?
        if not thread_running[thread_id]:
            print(fct_download_video.__name__, "Thread [" + str(thread_id) + "] has been stopped")
            data_dict['progress'] = 'Stopped By User'
            data_dict['step'] = 'Aborted'
            data_dict['action'] = 'none'
            data_dict['format'] = ''
            data_dict['format_desc'] = ''
            socketio.send(data_dict, json=True, to=sid)
            return

        # looking for an error
        if "error" in process_out or "ERROR" in process_out:
            print(fct_download_video.__name__, "Error detected line:" + process_out)
            data_dict['step'] = 'Error'
            data_dict['progress'] = process_out
            data_dict['action'] = 'false'
            data_dict['format'] = ''
            data_dict['format_desc'] = ''
            socketio.send(data_dict, json=True, to=sid)
            return

        # looking for "destination" file name
        if " Merging formats into " in process_out:
            l_output_filename = process_out.split(" Merging formats into ", 1)[1]
            l_output_filename = os.path.basename(l_output_filename)
            l_output_filename = l_output_filename.strip('"')
            l_output_filename = re.sub(r'.f\d{2}.', '', l_output_filename)
            print(fct_download_video.__name__, "Destination out found :[" + str(l_output_filename) + "]")
            data_dict['output_filename'] = l_output_filename
            data = json.dumps(data_dict)

        if "[ExtractAudio] Destination:" in process_out:
            l_output_filename = process_out.split(" Destination: ", 1)[1]
            l_output_filename = os.path.basename(l_output_filename)
            l_output_filename = l_output_filename.strip('"')
            l_output_filename = re.sub(r'.f\d{2}.', '', l_output_filename)
            print(fct_download_video.__name__, "Destination out found :[" + str(l_output_filename) + "]")
            data_dict['output_filename'] = l_output_filename
            data = json.dumps(data_dict)

        # looking for "destination" file name (already downloaded file)
        if "has already been downloaded" in process_out:
            l_output_filename = re.split("\[download\] | has already been downloaded", process_out)[1]
            l_output_filename = os.path.basename(l_output_filename)
            l_output_filename = re.sub(r'.f\d{2}.', '', l_output_filename)
            print(fct_download_video.__name__, "Destination out found :[" + l_output_filename + "]")
            data_dict['output_filename'] = l_output_filename
            data = json.dumps(data_dict)

        # detect end of process
        if not process_out and float(end - start) < float(0.00003):
            print(fct_download_video.__name__, "End of process")
            if "generic" in last_sent_process_out or last_sent_process_out == "":
                data_dict['step'] = 'Error'
                data_dict['progress'] = "Something bad happened ¯\_(ツ)_/¯"
                data_dict['action'] = 'false'

            else:
                data_dict['step'] = 'Done'
                data_dict['progress'] = last_sent_process_out
                data_dict['action'] = 'download'

            socketio.send(data_dict, json=True, to=sid)
            return
        else:
            data_dict['step'] = "Processing " + ("." * proccessing)
            socketio.send(data_dict, json=True, to=sid)

        # ignore some string # send only delta
        if not "Deleting original file download" in process_out \
                and last_sent_process_out != process_out and process_out:
            data_dict['progress'] = process_out
            socketio.send(data_dict, json=True, to=sid)
            last_sent_process_out = process_out
        else:
            print(fct_download_video.__name__, "Hey, there are totally identical !!!")

# main function
if __name__ == '__main__':

    enablePrint()
    print("O.S Name:", os.name, file=sys.stderr)


    create_app()
