from ModuleBase import Module #, Async_Task, AsyncModuleManager
from pubsub import pub
import asyncio
import Gripper 

class Servo(Module):
    def __init__(self, device, address, pos, minimum, maximum, increment):
        super().__init__()
        self.device = device
        self.inc = 0
        self.increment = int(increment)
        self.pos = int(pos)
        self.prev = self.pos
        self.min = 500 if int(minimum) < 500 else int(minimum)
        self.max = 2500 if int(maximum) > 2500 else int(maximum)
        self.address = address
        exec(f'pub.subscribe(self.Listener, "gamepad.{self.device}")')

    def run(self):
        if self.inc == 0:
            return
        self.pos += self.inc
        if self.pos > self.max: self.pos = self.max
        if self.pos < self.min: self.pos = self.min
        pub.sendMessage('can.send', message = {"address": eval(self.address), "data": [0x40, self.pos >> 8 & 0xff, self.pos & 0xff]})

    def Listener(self, message):
        tool_state = message["tool_state"]

        if tool_state == 1:
            self.inc = +self.increment
        elif tool_state == -1:
            self.inc = -self.increment 
        else:
            self.inc = 0

class __Test_Case_Send__(Module):
    def __init__(self):
        super().__init__()
        pub.subscribe(self.Listener, "can.send")

    def run(self):
        pub.sendMessage("gamepad.gripper", message = {"extend": False, "retract": True})

    def Listener(self, message):
        print(message)

# if __name__ == "__main__":

#     Gripper = Gripper('gripper', '0x21', 17000)
#     Gripper.start(1)
#     __Test_Case_Send__ = __Test_Case_Send__()
#     __Test_Case_Send__.start(1)
#     AsyncModuleManager = AsyncModuleManager()
#     AsyncModuleManager.register_modules(Gripper, __Test_Case_Send__)

#     try:
#         AsyncModuleManager.run_forever()
#     except KeyboardInterrupt:
#         pass
#     except BaseException:
#         pass
#     finally:
#         print("Closing Loop")
#         AsyncModuleManager.stop_all()
