from ModuleBase import Module
from pubsub import pub

class Tempsensor(Module):
 def __init__(self, device, address, calibration):
   super().__init__()
   self.device = device
   self.address = address
   self.calibration = float(calibration)
   self.received_data = None
   exec(f'pub.subscribe(self.Listener, "gamepad.{self.device}")')

 def run(self):
  pub.sendMessage('ethernet.send', message = {"type": "CAN", "address": eval(self.address), "data": [10, 0x00, 0x00]}) 
  pub.subscribe(self.data_received, "can.data")

 def data_received(self, data):
        self.received_data = data
        print(self.received_data)
