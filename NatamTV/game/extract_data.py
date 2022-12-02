import socket
from PIL import Image
import pytesseract
import requests
import cv2
import magic
import re
from datetime import timedelta
import hashlib
import time
from typing import *

HOST = "127.0.0.1"  # localhost
PORT = 65432  # non-privileged ports are > 1023

CHANNEL_STREAM_DIRS = {
    "Knesset": {
        "root_url": "https://contact.gostreaming.tv/Knesset/myStream",
        "playlist": "playlist.m3u8",
        "bitrate": 0, # TODO: check possibility of using this value and retreiving it automatically
        "chunk_duration": 0 # TODO: check possibility of using this value and retreiving it automatically
    }
}

BG_FILEDIR = "images\\channel currframe.png"
RESPONSE_FILENAME = "response.ts"


def get_streams(channel: str) -> str:
    response = requests.get(f"{CHANNEL_STREAM_DIRS[channel]['root_url']}/{CHANNEL_STREAM_DIRS[channel]['playlist']}", verify=False)
    return response.text


def get_chunklist_url(streams: str) -> str:
    lines = streams.split('\n')
    for line in lines:
        if line.endswith('.m3u8'):
            return line
    return None


def get_chunks_from_chunklist(channel, chunklist_url: str):
    response = requests.get(f"{CHANNEL_STREAM_DIRS[channel]['root_url']}/{chunklist_url}", verify=False)
    return response.text


def choose_chunk_name(playlist_response: str) -> str:
    lines = playlist_response.split('\n')
    for line in lines:
        if line.endswith('.ts'):
            return line
    return None


def get_chunk(channel: str, chunk_name: str):
    response = requests.get(f"{CHANNEL_STREAM_DIRS[channel]['root_url']}/{chunk_name}", verify=False)
    with open(RESPONSE_FILENAME, "wb") as f:
        f.write(response.content)


def chunk_hash():
    return hashlib.md5(open(RESPONSE_FILENAME, 'rb').read()).hexdigest()


def relevant_chunk_frame(delta: timedelta):
    # Read transportstream
    vc = cv2.VideoCapture(RESPONSE_FILENAME)

    # Retreieve TS properties
    frames = vc.get(cv2.CAP_PROP_FRAME_COUNT)
    framerate = vc.get(cv2.CAP_PROP_FPS) # TODO: check for better way to find out framerate. Could be constant?
    video_time = round(frames / framerate) # TODO: check for better way to find out duration. Could be constant?

    # Calculate requested frame and set TS to new frame
    requested_frame = 2 if delta.seconds > video_time else delta.seconds * framerate
    vc.set(cv2.CAP_PROP_POS_FRAMES, requested_frame-1)

    # Read frame
    rval , frame = vc.read()
    
    # Write and resize frame. TODO: check if can resize frame ndarray instead of resizing an already written file
    cv2.imwrite(BG_FILEDIR, frame)
    img = Image.open(BG_FILEDIR).resize((1920, 1080))
    img.save(BG_FILEDIR)


def get_frame_dimensions():
    t = magic.from_file(BG_FILEDIR)
    return list(map(int, re.search('(\d+) x (\d+)', t).groups()))


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Open socket and listen to clients
    s.bind((HOST, PORT))
    s.listen()
    # Accepting incoming connection
    conn, addr = s.accept()
    with conn: # Client communication logic
        # Initialize logic
        print(f"Connected by {addr}")
        response_hash = ""
        t1 = time.time()
        delta = timedelta(seconds=0)
        # Communication loop
        while True:
            # Getting recent chunk from requested channel
            streams = get_streams("Knesset")
            chunklist_url = get_chunklist_url(streams)
            chunk = choose_chunk_name(get_chunks_from_chunklist("Knesset", chunklist_url))
            print("found chunk")
            get_chunk("Knesset", chunk)
            print("downloaded chunk")

            # Calculating desired second from video chunk
            checking_hash = chunk_hash()
            delta = delta+timedelta(seconds=time.time()-t1) if response_hash == checking_hash else timedelta(seconds=1)
            response_hash = checking_hash
            print(delta)

            # Extracting frame from chunk
            relevant_chunk_frame(delta)
            print("got relevant chunk frame")
            
            # Cropping frame for OCR # TODO: research better ways to find subtitles
            DIMENSIONS = get_frame_dimensions()
            print("got frame dimensions")
            box = (0, DIMENSIONS[1]/5*4, DIMENSIONS[0], DIMENSIONS[1])
            img = Image.open(BG_FILEDIR).crop(box=box)
            print("cropped frame")
            
            # Sending frame to OCR
            data = pytesseract.image_to_string(img, lang="heb").replace('\n', '').replace('"', '').encode()
            if data.decode() == '':
                data = "Couldn't get CCs".encode()
            print("ocr'd frame")

            # Sending subtitles to VN client
            print(data.decode())
            conn.sendall(data)

            # Waiting for client answer
            t1 = time.time()
            a = conn.recv(1024)
            print(a)
