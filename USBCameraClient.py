import cv2 as cv
import struct
import socket
import time 
from ModuleBase import Module
from pubsub import pub

class USBCamera(Module):
    def __init__(self, cam_num, cam_format, v_width, v_height, v_fps):
        super().__init__()

        # self.HOST = "169.254.196.165"  # Isaac's Laptop
        self.HOST = '169.254.243.121' # Silver Laptop 
        self.PORT = 8080
        self.connected = False

        self.cam = cv.VideoCapture(cam_num, cv.CAP_V4L2)

        # Set the video format
        self.cam.set(cv.CAP_PROP_CONVERT_RGB, 0)
        fourcc = cv.VideoWriter_fourcc(*cam_format)
        self.cam.set(cv.CAP_PROP_FOURCC, fourcc)
        # self.cam.set(cv.CAP_PROP_HW_ACCELERATION, cv.VIDEO_ACCELERATION_ANY)
        self.cam.set(cv.CAP_PROP_FRAME_WIDTH, v_width)
        self.cam.set(cv.CAP_PROP_FRAME_HEIGHT, v_height)
        self.cam.set(cv.CAP_PROP_FPS, v_fps)

        self.connect_to_server()
    
    def connect_to_server(self):
        while True:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.socket.connect((self.HOST, self.PORT))

                print(f"Connected to USB server {self.HOST}")
                self.connected = True
                break
            except ConnectionRefusedError:
                print('No USB server connection established. Retrying in 3 seconds...')
                time.sleep(3)
    

    def run(self):
        # Read the frame
        ret, image = self.cam.read()
        # Convert the frame to a byte array
        frame_data = image.tobytes()
        
        if self.connected and self.socket is not None:
        
            try:
                # Send the frame data through the socket
                self.socket.sendall(struct.pack('<L', len(frame_data)) + frame_data)
                # print(f"frame data: {frame_data}, frame")

            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                print('USB Server connection lost. Reconnecting...')
                self.socket.close()
                self.connected = False
                self.socket = self.connect_to_server()
        else:
            self.connect_to_server()



if __name__ == "__main__":
    USBCamera = USBCamera(0, 'MJPG', 1280, 720, 30)
    USBCamera.start(60)
