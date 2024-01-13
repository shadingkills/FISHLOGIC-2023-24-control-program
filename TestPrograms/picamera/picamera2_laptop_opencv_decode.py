# laptop side script
# record to stream with opencv to decode

import io
import socket
import struct
import cv2

# Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
# all interfaces)
server_socket = socket.socket()
server_socket.bind(('', 8000))
server_socket.listen()

# # Accept a single connection and make a file-like object out of it
connection, addr = server_socket.accept()

print(f"connected to {addr}")

# connection = connection.makefile('rb')

try:
    video = cv2.VideoCapture(f"tcp://169.254.89.178:8000/")
    while True:
        ret,frame = video.read()
        cv2.imshow("frame", frame)
        cv2.waitKey(0)


finally:
    pass
    # connection.close()
    # server_socket.close()