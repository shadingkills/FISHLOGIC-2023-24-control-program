# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
from datetime import datetime
import board
import adafruit_bno055
from ModuleBase import Module


class IMUReaderPi(Module):
    def __init__(self):
        super().__init__()

        i2c = board.I2C()
        self.sensor = adafruit_bno055.BNO055_I2C(i2c)
        self.last_val = 0xFFFF
        localTime = time.strftime('%Y-%m-%d, %H-%M-%S')

        self.file = open('./IMUData/IMU_Data ' + localTime + '.txt', 'w')
        self.file.write("Temp (c), Acc\n")
        print("IMU Reading")
    
    def temperature(self):
        result = self.sensor.temperature
        if abs(result - self.last_val) == 128:
            result = self.sensor.temperature
            if abs(result - self.last_val) == 128:
                return 0b00111111 & result
        self.last_val = result
        return result
    
    def run(self):
        sys, gyro, accel, mag = self.sensor.calibration_status
        print("calibration status: {}".format(self.sensor.calibration_status))
        self.file.write("(" + str(self.temperature()) +")\t" + \
                        str(self.sensor.acceleration) + "\t" + \
                        str(self.sensor.magnetic) +"\t" + \
                        str(self.sensor.gyro)+ "\t" + \
                        str(self.sensor.euler)+"\t" + \
                        str(self.sensor.quaternion)+"\t" + \
                        str(self.sensor.linear_acceleration)+"\t" + \
                        str(self.sensor.gravity)+ "\t("+ \
                        str(sys)+",\t"+str(gyro)+",\t"+str(accel)+",\t"+str(mag)+ ")\t(" +  \
                        str(time.time()) +")\t(\n"
                        )