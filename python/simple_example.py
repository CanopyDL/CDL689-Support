from imu_driver import *

imu = imu_device()
imu.open('/dev/cu.usbserial-AM00KH14')
imu.start_stream()

t0=time.time()
while (time.time()-t0)<5:
    # print('hi')
    imu.tasks()
    # time.sleep(.1)
    # if round(time.time()-t0,1)
    print(imu.gyro[0])


imu.stop_stream()
imu.close()

