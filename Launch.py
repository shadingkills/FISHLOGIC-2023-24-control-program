
import sys
from ModuleBase import ModuleManager
from PyGameServices import PyGameServices

# MODULES
from GUI import GUI
from Joystick import Joystick
from ControlProfile import ControlProfile
from ThrusterPower import ThrusterPower
from Thrusters import Thrusters
from Logger import Logger
from EthernetServer import EthernetHandler
from EthernetServer import TestEthernetHandler
#from USBCameraServer import USBCameraHandler, USBCameraDisplay
from EM import EM
from Gripper import Gripper
from Servo import Servo
import os
import time 
from Actuator import Actuator

# allow pygame to not be in focus and still works
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

mm = ModuleManager()

pygs = PyGameServices()
pygs.start(100)
pygame = pygs.get_pygame()

GUI = GUI()
Joystick = Joystick()
ControlProfileA = ControlProfile(100, 30, "A")
ControlProfileB = ControlProfile(70, 50, "B")
ControlProfileC = ControlProfile(50, 50, "C")
ControlProfileD = ControlProfile(30, 50, "D")
ThrusterPower = ThrusterPower()
Thrusters = Thrusters()
EthernetHandler = EthernetHandler()
TestEthernetHandler = TestEthernetHandler()
Logger = Logger(False, False, None, "ethernet.send") # FILE, PRINT, RATE_LIMITER, TOPICS
EM1 = EM("EM1", "0x32") # change address here
EM2 = EM("EM2", "0x33") # change address here........................................
Gripper = Gripper("gripper", "0x21", "10000", True)
Actuator = Actuator("actuator", "0x20", "10000")
#Gripper = Servo("gripper","0x43", "1100", "800", "1800", "24")


# REGISTERING MODULES (INSTANCE, REFRESH PER SECOND)
mm.register(
            (GUI, 60),
            (Joystick, 60),
            (ControlProfileA, 1),
            (ControlProfileB, 1),
            (ControlProfileC, 1),
            (ControlProfileD, 1),
            (ThrusterPower, 60),
            (Thrusters, 10),
            (EthernetHandler, 120),
            (EM1, 5),
            (EM2, 5),
            (Actuator, 5),
            (Gripper, 10),
            # (TestEthernetHandler, 15),
)

try:
    # main thread

    mm.start_all()

    run = True
    while run:
        for event in pygame.event.get(): # pygame event loop must run in the main thread
            if event.type == pygame.QUIT:
                run = False
        time.sleep(0.015)
except KeyboardInterrupt:
    pygame.display.quit() 
    pygame.quit()
    mm.stop_all()
    print("stopped all modules")
    sys.exit()
finally:
    pygame.display.quit()
    pygame.quit()
    mm.stop_all()
    #TODO: stuck at stopping ethernet client handler, blocking call socket.accept() 
    print("stopped all modules")
    sys.exit()
