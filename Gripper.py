from ModuleBase import Module
from pubsub import pub

class Gripper(Module):
    def __init__(self, device, address, speed, flip):
        super().__init__()
        self.device = device
        self.speed = int(speed)
        self.address = address
        self.flip = flip
        exec(f'pub.subscribe(self.Listener, "gamepad.{self.device}")')
        self.tool_state = 0

    def run(self):
        if self.flip:
            self.tool_state = -self.tool_state
            
        if self.tool_state == 1:
            pub.sendMessage('ethernet.send', message = {"type": "CAN", "address": eval(self.address), "data": [32, self.speed >> 8 & 0xff, self.speed & 0xff]})
        elif self.tool_state == -1:
            pub.sendMessage('ethernet.send', message = {"type": "CAN", "address": eval(self.address), "data": [32, -self.speed >> 8 & 0xff, -self.speed & 0xff]})
        else:
            pub.sendMessage('ethernet.send', message = {"type": "CAN", "address": eval(self.address), "data": [32, 0x00, 0x00]})

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

if __name__ == "__main__":
    pass
