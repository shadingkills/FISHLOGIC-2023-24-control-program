from ModuleBase import Module
from pubsub import pub

EMLRcommand = {
                "EM_L": {1 : [0x30, 0x10], 0: [0x30, 0x00]},
                "EM_R": {1 : [0x31, 0x10], 0: [0x31, 0x00]},
                }

class EM(Module):
    def __init__(self, device, address):
        super().__init__()
        self.device = device
        self.address = address
        self.data_L = None
        self.data_R = None
        exec(f"pub.subscribe(self.Listener, 'gamepad.{self.device}')")

    def run(self):
        #print(self.address, self.data_L, self.data_R)
        if self.data_L is not None:
            # if self.data_L is 0:
            #     pub.sendMessage("ethernet.send", message = {"type": "CAN", "address": eval(self.address), "data": self.data_L})
                
            pub.sendMessage("ethernet.send", message = {"type": "CAN", "address": eval(self.address), "data": self.data_L})
        
        if self.data_R is not None:
            pub.sendMessage("ethernet.send", message = {"type": "CAN", "address": eval(self.address), "data": self.data_R})

    def Listener(self, message):
        self.data_L = EMLRcommand["EM_L"][1 if message["L"] else 0]
        self.data_R = EMLRcommand["EM_R"][1 if message["R"] else 0]

class __Test_Case_Send__(Module):
    def __init__(self):
        super().__init__()
        pub.subscribe(self.Listener, "ethernet.send")

    def run(self):
        pub.sendMessage("gamepad.EM1", message = {"L": True, "R": False})

    def Listener(self, message):
        print(message)

if __name__ == "__main__":
    pass
