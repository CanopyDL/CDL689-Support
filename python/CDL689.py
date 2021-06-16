import serial
from pymodbus.client.sync import ModbusSerialClient
import numpy as np

UNIT = 0x01

def twos_comp(val, bits):
    """compute the 2's compliment of int value val"""
    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)  # compute negative value
    return val

class CDL689:
    def __init__(self):
        self.connect = 0
        self.stream = 0
        self.sentence = b''
        self.buffer_length = 100
        self.acc = np.zeros((3, self.buffer_length), dtype=np.int)
        self.gyro = np.zeros((3, self.buffer_length), dtype=np.int)

    def open(self,port):
        self.ser = serial.Serial(port, 230400, timeout=0)
        self.mod = ModbusSerialClient(port=port, baudrate=230400, method="RTU")
        self.connect=1
        self.mod.write_register(10, 0x96, unit=UNIT)  # stop streaming

        # setup accelerometer
        self.mod.write_register(3, 0x50, unit=UNIT)  # data
        self.mod.write_register(2, 0x10, unit=UNIT)  # IMU register

        # setup gyro
        self.mod.write_register(3, 0x50, unit=UNIT)  # data
        self.mod.write_register(2, 0x11, unit=UNIT)  # IMU register

        self.mod.write_register(1, 0x0F, unit=UNIT)  # WHO AM I
        rr = self.mod.read_holding_registers(3, 1, unit=UNIT)
        print(rr.registers[0])

    def close(self):
        self.connect = 0
        self.ser.close()
        self.mod.close()

    def start_stream(self):
        self.mod.write_register(10, 0x69, unit=UNIT)  # start streaming
        self.stream = 1

    def stop_stream(self):
        self.mod.write_register(10, 0x96, unit=UNIT)  # start streaming
        self.stream = 0

    def setUpdateRate(self, newRate):
        #set the period of the stream timer in microseconds
        self.mod.write_register(11, newRate, unit=UNIT)  # start streaming

    def tasks(self):
        if self.connect and self.stream:
            if (self.ser.inWaiting() > 0):
                self.sentence += self.ser.read(50)
                vals = self.sentence.split(b'\x55\xAA')
                for i in range(len(vals) - 1):
                    val = vals[i]
                    if len(val) > 0:
                        self.gyro = np.roll(self.gyro, 1)
                        self.gyro[0, 0] = twos_comp(int.from_bytes(val[0:2], byteorder='little'),16)
                        self.gyro[1, 0] = twos_comp(int.from_bytes(val[2:4], byteorder='little'),16)
                        self.gyro[2, 0] = twos_comp(int.from_bytes(val[4:6], byteorder='little'),16)
                        self.acc = np.roll(self.acc, 1)
                        self.acc[0, 0] = twos_comp(int.from_bytes(val[6:8], byteorder='little'),16)
                        self.acc[1, 0] = twos_comp(int.from_bytes(val[8:10], byteorder='little'),16)
                        self.acc[2, 0] = twos_comp(int.from_bytes(val[10:12], byteorder='little'),16)

                self.sentence = vals[-1]
