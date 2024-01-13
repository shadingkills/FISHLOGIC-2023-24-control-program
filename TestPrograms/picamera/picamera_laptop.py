# Import necessary packages
import cv2
import numpy as np
import socket
import struct
import pickle

# Set the IP address and port to use for the incoming connection
ip_address = '169.254.196.165'
port = 8485

# Create a socket and bind it to the IP address and port
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((ip_address, port))
server_socket.listen()

# Accept a single connection and make a file-like object out of it
client_socket, addr = server_socket.accept()
print(f"connected to {addr}")
connection = client_socket.makefile('rb')

try:
    while True:
        # Retrieve message size
        message_size = struct.unpack("L", connection.read(struct.calcsize("L")))[0]
        data = connection.read(message_size)
        frame = pickle.loads(data)

        # Perform any OpenCV operations on the frame here
        # For example, let's just convert the image to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Display the resulting frame
        cv2.imshow('frame', gray)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    cv2.destroyAllWindows()
    connection.close()
    server_socket.close()
