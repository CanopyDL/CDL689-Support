#The CDL689 driver requires pymodbus.  To install:
# https://pymodbus.readthedocs.io/en/latest/readme.html#installing
# pip install  -U pymodbus

from CDL689 import *
import time

imu = CDL689()

#Windows
#imu.open('COM7')

#Linux/MacOS
imu.open('/dev/cu.usbserial-AD0K5L6R')

print("Temperature:")
print(imu.readTemperature())

imu.setUpdateRate(10000)

#uncomment this section to stream data for a fixed period of time
# imu.start_stream()
# t0=time.time()
# while (time.time()-t0) < 10: #stream for one second
#     imu.tasks()
#     #print(imu.gyro[0])
#     print(imu.temp)
# imu.stop_stream()

imu.close()

