#The CDL689 driver requires pymodbus.  To install:
# https://pymodbus.readthedocs.io/en/latest/readme.html#installing
# pip install  -U pymodbus

from CDL689 import *
import time
import sys

imu = CDL689()

#Windows
#imu.open('COM7')

#Linux/MacOS
imu.open('/dev/cu.usbserial-AD0K5L6R')
imu.setSamplesPerFrame(10)
imu.setUpdateRate(200) #microseconds

imu.setBaudRate(650000)

print("Unique ID:")
print(imu.readUniqueId())
#sys.exit()


print("Temperature:")
print(imu.readTemperature())
#sys.exit()
#
# #uncomment this section to stream data for a fixed period of time
imu.start_stream()
t0=time.time()
while (time.time()-t0) < 5: #stream for one second
    imu.tasks()
    #print("Gyro:")
    #print(imu.gyro[0])
    # print("Acc:")
    # print(imu.acc[0])
    #print(imu.temp)
imu.stop_stream()

imu.setBaudRate(9600)   #set the baud rate back to the default 9600 so we can run again without a hard reset
imu.close()

