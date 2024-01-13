#!/usr/bin/python3

import socket
import time
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

picam2 = Picamera2()
video_config = picam2.create_video_configuration({"size": (1280, 720)})
picam2.configure(video_config)
encoder = H264Encoder(1000000)

with socket.socket() as sock:
    sock.connect(("169.254.196.165", 8000))
    print("connected")
    stream = sock.makefile("wb")
    
    picam2.start_preview()
    time.sleep(2)
    
    
    picam2.start_recording(encoder, FileOutput(stream))
    time.sleep(20)
    picam2.stop_recording()
