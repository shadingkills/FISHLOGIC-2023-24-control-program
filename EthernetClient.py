import time
import socket
import struct
from pubsub import pub
from ModuleBase import Module

class EthernetClient(Module):
    def __init__(self):
        super().__init__()

        # self.HOST = "169.254.196.165"  # Isaac's Laptop
        #self.HOST = '169.254.243.121' # Silver Laptop 
        self.HOST = "169.254.123.187" #TUF laptop
        #self.HOST = "" #lenovo laptop
        self.PORT = 226  # The port used by the server

        self.connect_to_server()

        pub.subscribe(self.message_listener, "ethernet.send")

    def connect_to_server(self):
        while True:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.HOST, self.PORT))

                print(f"Connected to server {self.HOST}")
                break
            except ConnectionRefusedError:
                print('No connection established. Retrying in 3 seconds...')
                time.sleep(3)
        
    
    def message_listener(self, message):

        if message["type"] == "CAN":

            START = "X".encode()
            message_type = "CAN".encode()

            address1 = message["address"] >> 8 & 0xff
            address2 = message["address"] & 0xff

            if message["data"] == []:
                
                data = [address1] + [address2] + [0]
            else:
                data = [address1] + [address2] + message["data"]

            format_string = format_string = f"1s1B3s{len(data)}B"

            data_bytes = struct.pack(format_string, START, len(data), type, *data)
        
        elif message["type"] == "TST":

            START = "X".encode()
            type = "TST".encode()
            
            time_byte = struct.pack("d", message["data"])
            data_bytes = struct.pack("1s1B3s", START, len(time_byte), type)
            data_bytes = data_bytes + time_byte

        else: # LID, SON, IMU
            pass

        try:
            self.socket.sendall(data_bytes)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            self.socket.close()
            print(f"Disconnected from {self.HOST}")
            self.connect_to_server()

    # receive
    def run(self):
        try:
            data_receive = self.socket.recv(5) # get 2 bytes first, X start of frame, 1 integer length of frame

            if data_receive:
                data = struct.unpack(f"1s1B3s", data_receive)
                if data[0].decode() == "X":
                    frame_length = data[1]
                    type = data[2].decode()
                else:
                    frame_length = 0
            else:
                frame_length = 0
            
            data_frame = self.socket.recv(frame_length)

            if data_frame:

                if type == "CAN":
                    data = struct.unpack(f"{frame_length}B", data_frame)
                    address, data = data[0], data[1:]
                    pub.sendMessage("can.send", message = {"address": address, "data": data})

                elif type == "TST":
                    data = struct.unpack("d", data_frame)
                    time_rec = data[0]
                    pub.sendMessage("ethernet.send", message = {"type": "TST", "data": time_rec})
                
                else: # LID, SON, IMU
                    pass

        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            self.socket.close()
            print(f"Disconnected from {self.HOST}")
            self.connect_to_server()
        
if __name__ == "__main__":
    from CANHandler import CANHandler
    # from LidarReaderPi import LidarReaderPi
    # from IMUReaderPi import IMUReaderPi
    from USBCameraClient import USBCamera

    EthernetClient = EthernetClient()
    USBCamera = USBCamera(0, 'MJPG', 1280, 720, 30)
    CANHandler = CANHandler(250000)

    EthernetClient.start(120)
    USBCamera.start(60)
    CANHandler.start(30)


    # LidarReaderPi = LidarReaderPi()
    # LidarReaderPi.start(1)

    # IMUReaderPi = IMUReaderPi()
    # IMUReaderPi.start(100)

    
    



