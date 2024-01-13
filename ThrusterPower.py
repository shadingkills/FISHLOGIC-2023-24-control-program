'''
Subcribe Topics:

control.movement
    message: Strafe, Drive, Yaw, UpDown, TiltFB, TiltLR <Vector6: -1, 1>

Publish Topics:

control_movement
    messsage: FL, FR, BL, BR, UF, UB <-1, 1>
'''

from ModuleBase import Module
from pubsub import pub
import numpy as np
import yaml
import time

#Scale constants
Scale_Constants = [1,1,1,1,1,1,1]


class ThrusterPower(Module):
    def __init__ (self):
        super().__init__()
        try:
            content = yaml.load(open('Thruster_Hydron.yaml', 'r'), Loader = yaml.FullLoader)
            for key,value in content.items():
                exec(f"self.{key} = value")
        except FileNotFoundError:
            pass

        self.CG = np.array(tuple(map(float, self.CG.split(','))))
        self.ThrusterMatrix = np.zeros((6,1))
        self.Thrusters = (self.ThrusterFL, self.ThrusterFR, self.ThrusterBL, self.ThrusterBR, self.ThrusterUF, self.ThrusterUB)
        self.counter = 0
        self.finalList = None

        for Thruster in self.Thrusters: # 6x6 Matrix
            ThrusterPosition = np.array(tuple(map(float, Thruster["Position"].split(','))))
            ThrusterDirection = np.array(tuple(map(float, Thruster["Direction"].split(','))))
            ThrusterPosition = np.subtract(ThrusterPosition, self.CG)
            Torque = np.cross(ThrusterPosition, ThrusterDirection)
            ThrusterArray = np.concatenate((ThrusterDirection, Torque)).reshape(6,1)
            self.ThrusterMatrix = np.concatenate((self.ThrusterMatrix, ThrusterArray), axis = 1)

        for i in range(6):
            message = [0] * 6
            message[i] = -1
            self.gamepadScaleConstant(message = {"control_movement": message})
        self.gamepadScaleConstant(message = {"control_movement": [0,0,0,1,0,0]})

        pub.subscribe(self.command_movement, "control.movement")

    def truncate(self, finalList):
        if max(abs(finalList)) > 1:
            for counter, Thruster in enumerate(self.Thrusters):
                finalList[counter, 0] /= max(abs(finalList))
        return finalList

    def directionScale(self, finalList):
        for counter, Thruster in enumerate(self.Thrusters):
            if finalList[counter, 0] < 0:
                finalList[counter, 0] *= Thruster["NegativeScale"]
            else:
                finalList[counter, 0] *= Thruster["PositiveScale"]
            #finalList[counter,0] /= Thruster["Scale"] # uncomment for combinational movement
            if Thruster["Invert"] == True:
                finalList[counter, 0] *= -1
        return finalList

    def invert(self, finalList):
        for counter, Thruster in enumerate(self.Thrusters):
            if Thruster["Invert"] == "True":
                finalList[counter, 0] *= -1
        return finalList

    def overallScale(self, finalList):
        for counter, Thruster in enumerate(self.Thruster):
            finalList[counter, 0] /= Thruster["Scale"]

    def pseudoInv(self, expectedResult):
        ThrusterMatrixInv = np.linalg.pinv(self.ThrusterMatrix[0:6,1:7])
        finalList = ThrusterMatrixInv.dot(expectedResult)
        return finalList

    def gamepadScale(self, message):
        gamepadScaled = list(message["control_movement"])
        for counter, dof in enumerate(gamepadScaled):
            if counter == 3 and dof > 0:
                gamepadScaled[counter] *= Scale_Constants[6]
            else:
                gamepadScaled[counter] *= Scale_Constants[counter]
        return gamepadScaled

    def gamepadScaleConstant(self, message):
        Strafe, Drive, Yaw, Updown, TiltFB, TiltLR = message["control_movement"]
        expectedResult = np.array((Strafe, Drive, Updown, TiltFB, TiltLR, Yaw)).reshape(6,1)
        finalList = self.pseudoInv(expectedResult)
        finalList = self.directionScale(finalList)
        for counter, dof in enumerate(message):
            if dof != 0 and max(abs(finalList)) != 0:
                Scale_Constants[self.counter] = float(1/max(abs(finalList)))
        self.counter += 1

    def command_movement(self, message):

        message = self.gamepadScale(message)
        Strafe, Drive, Yaw, Updown, TiltFB, TiltLR = message
        expectedResult = np.array((Strafe, Drive, Updown, TiltFB, TiltLR, Yaw)).reshape(6,1)
        finalList = self.pseudoInv(expectedResult)
        finalList = self.directionScale(finalList)
        # finalList = self.invert(finalList)
        ############ inverted from thruster desired direction to thrust direction
        finalList = self.truncate(finalList)

        finalList = finalList.reshape(1,6)
        finalList = finalList.tolist()
        self.finalList = [item for item in finalList if isinstance(item,list)]
        

    def run(self):
        if self.finalList is not None:
            pub.sendMessage("thruster.power", message = {"thruster_power": self.finalList})

class __Test_Case_Single__(Module):
    def __init__(self):
        super().__init__()
        pub.subscribe(self.Thruster_Power_Listener_Single, "thruster.power")

    def Thruster_Power_Listener_Single(self, message):
        print("message: ", message["thruster_power"])

    def run(self):
        time.sleep(1)
        pub.sendMessage("control.movement", message = {"control_movement": (0,1,0,1,0,0)})


if __name__ == "__main__":
    __Test_Case_Single__ = __Test_Case_Single__()
    ThrusterPower = ThrusterPower()

    ThrusterPower.start(1)
    __Test_Case_Single__.start(1)
