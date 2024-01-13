
'''
CAN_Handler Module

Subscribe Topics:

can.send
    "address": <hexadecimal>
    "data" <bytearrray>

Publish Topics:

log.sent:
    message frame

can.receive.<arbitration_id>:
    "data" <bytearray>
    "extra" <dictionary>
	"timestamp" <float>

'''


import can
from ModuleBase import Module
import sys
from pubsub import pub
import threading


class CANHandler(Module):
    def __init__(self, baudrate):
        super().__init__()
        
        self.baudrate = baudrate
        self.lock = threading.Lock()

        if sys.platform == 'win32':

            import at_serial_can
            from infi.devicemanager import DeviceManager

            connected = False
            self.port = None

            dm = DeviceManager()
            dm.root.rescan()
            for d in dm.all_devices:
                if "USB-SERIAL CH340" in d.description:
                    self.port = "COM" + d.description[-2]
                    self.bus = at_serial_can.ATSerialBus(channel= self.port, ttyBaudrate=self.baudrate, bitrate= self.baudrate)
                    print(f"Connected {self.port}")
                    connected = True
            
            if not connected:
                raise Exception("NOT Connected to any CAN BUs sender, goodbye, check cable")
        
        if sys.platform == 'linux':

            self.bus = can.interface.Bus(bustype = "socketcan", channel = "can0", bitrate = self.baudrate)

        pub.subscribe(self.message_listener, "can.send")
    

    def message_listener(self, message):
        msg = can.Message(arbitration_id = message["address"], data = message["data"], is_extended_id = False)

        self.lock.acquire()

        try:
            self.bus.send(msg, timeout=0.01)
        except Exception as e:
            print("Message not sent:", [e, msg])
        finally:

            self.lock.release()

    def run(self):
        msg = self.bus.recv(0)

        if msg is not None:

            data = msg.data
            data_array = [int.from_bytes(byte, byteorder='big') for byte in data]

            pub.sendMessage("ethernet.send", message = {"type": "CAN", "address": msg.arbitration_id, "data": data_array})

if __name__ == "__main__":
    CANHandler = CANHandler(250000)
