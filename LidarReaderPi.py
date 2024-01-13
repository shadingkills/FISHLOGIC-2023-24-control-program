#!/usr/bin/env python3
'''Records measurments to a given file. Usage example:

$ ./record_measurments.py out.txt'''
from rplidar import RPLidar
import time
from ModuleBase import Module


PORT_NAME = '/dev/ttyUSB0'

class LidarReaderPi(Module):
    def __init__(self):
        super().__init__()

        self.localtime = time.strftime('%Y-%m-%d, %H-%M-%S')
        
        self.lidar = RPLidar(PORT_NAME)
        self.outfile = open("./LidarData/Lidar_Data " + self.localtime + '.txt', 'w')
    
    def run(self):
    
        try:
            print("Lidar Measuring")
            for measurment in self.lidar.iter_measures():
                line = '\t'.join(str(v) for v in measurment)
                self.outfile.write(line + "\t" + str(time.time()) + '\n')
        except KeyboardInterrupt:
            print('lidar stop')
        self.lidar.stop()
        self.lidar.disconnect()
        self.outfile.close()
            
        
