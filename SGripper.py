from ModuleBase import Module
from pubsub import pub 
import Gripper

class Servo(Module):
    def __init__(self, device, address, pos, minimum, maximum, increment):
        super().__init__()
        self.inc = 0
        self.device = device
        self.increment = int(increment)
        self.pos = int(pos)
        self.prev = self.pos
        self.min = 500 if int(minimum) < 500 else int(minimum)
        self.max = 2500 if int(maximum) > 2500 else int(maximum)
        self.address = address
        exec(f'pub.subscribe(self.Listener, "gamepad.device")')
        
    def run(self):
        if self.pos > self.max: self.pos = self.max
        if self.pos < self.min: self.pos = self.min
        if self.tool_state == 1:
            self.pos += self.inc
            pub.sendMessage('ethernet.send', message = {"type": "CAN","address": eval(self.address), "data": [0x40, self.pos >> 8 & 0xff, self.pos & 0xff]})
        elif self.tool_state == -1:
            self.pos -= self.increment
        else:
            self.inc = 0
            
    def Listener(self, message):
        self.tool_state = message["tool_state"]
        
class __Test_Case_Send__(Module):
    def __init__(self):
        super().__init__()
        pub.subscribe(self.Listener, "ethernet.send")

    def run(self):
        pub.sendMessage("gamepad.gripper", message = {"extend": False, "retract": True})

    def Listener(self, message):
        print(message)