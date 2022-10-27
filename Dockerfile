# syntax=docker/dockerfile:1
FROM python:3.7-alpine
WORKDIR /code
ENV FLASK_APP=webui_yt_dlp.py
ENV FLASK_RUN_HOST=0.0.0.0
RUN apk add --no-cache gcc musl-dev linux-headers
COPY requirements.txt requirements.txt
# remove downloaded file every night at 3am
RUN crontab -l | { cat; echo "0 3 * * * bash rm -rf /code/download/*"; } | crontab -
RUN apk update
# download and install yt-dlp
RUN apk add git make zip
RUN git clone https://github.com/yt-dlp/yt-dlp
WORKDIR "/code/yt-dlp/"
RUN make yt-dlp && cp yt-dlp //usr/local/bin/
WORKDIR "/code/"
RUN apk add libffi-dev
RUN apk add ffmpeg
RUN pip3 install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 5000
COPY . .
CMD ["flask", "run"]
