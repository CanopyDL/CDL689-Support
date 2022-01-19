from CDL689 import *
import time

imu = CDL689()
imu.open('COM7')
imu.start_stream()

t0=time.time()
while (time.time()-t0)<5:
    imu.tasks()
    print(imu.gyro[0])

imu.stop_stream()
imu.close()

