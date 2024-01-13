# Import necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import socket
import struct
import pickle
import time

# Initialize the camera
camera = PiCamera()
rawCapture = PiRGBArray(camera)

# Allow the camera to warmup
time.sleep(0.1)

# Set the IP address and port of the laptop (receiver)
laptop_ip = '169.254.196.165'
laptop_port = 8485

# Create a socket and connect to the laptop
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((laptop_ip, laptop_port))
connection = client_socket.makefile('wb')

try:
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        img = frame.array
        data = pickle.dumps(img)
        # Send the size of the data first
        message_size = struct.pack("L", len(data)) # L stands for Long
        connection.write(message_size + data)
        rawCapture.truncate(0)
finally:
    connection.close()
    client_socket.close()
    camera.close()
