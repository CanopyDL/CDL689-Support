import serial
from pymodbus.client.serial import ModbusSerialClient
from pymodbus.framer import FramerType

import numpy as np
import time
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
        #self.sentence = b''
        self.sentence = bytearray()
        self.buffer_length = 100
        self.acc = np.zeros((3, self.buffer_length), dtype=np.int)
        self.gyro = np.zeros((3, self.buffer_length), dtype=np.int)
        self.CRC = 0
        self.frameCounter = 0
        self.temp = 0
        self.port = ''
        self.raw = np.zeros(self.buffer_length, dtype=np.int)
        self.baudRate = 9600
        self.samplesPerFrame = 1

    def open(self,port):
        self.port = port
        self.mod = ModbusSerialClient(port=port, baudrate=self.baudRate, framer=FramerType.RTU)
        self.connect=1
        self.mod.write_register(10, 0x96)  # stop streaming

        self.mod.write_register(1, 0x0F)  # WHO AM I
        self.mod.read_holding_registers(address=3, count=1)
        #print(rr.registers[0])

        # setup accelerometer
        self.mod.write_register(3, 0x50)  # data
        self.mod.write_register(2, 0x10)  # IMU register

        # setup gyro
        self.mod.write_register(3, 0x50)  # data
        self.mod.write_register(2, 0x11)  # IMU register

    def close(self):
        self.connect = 0
        #self.ser.close()
        self.mod.close()

    def start_stream(self):
        self.mod.write_register(10, 0x69)  # start streaming
        self.stream = 1
        #switch from ModBus to Serial
        self.mod.close()
        self.ser = serial.Serial(self.port, self.baudRate, timeout=0)

    def stop_stream(self):
        #self.ser.write(bytes([0x96]))   #send any random byte to kill the stream
        self.ser.close()
        self.mod = ModbusSerialClient(port=self.port, baudrate=self.baudRate, framer=FramerType.RTU)
        self.mod.write_register(10, 0x96)  # stop streaming
        self.stream = 0

    def setUpdateRate(self, newRate):
        #set the period of the stream timer in microseconds
        self.mod.write_register(11, newRate)  # start streaming

    def setBaudRate(self, newRate):
        # set the period of the stream timer in microseconds
        self.baudRate = newRate
        self.mod.write_register(12, int(newRate / 100))  # set baudrate (divide by 100 to fit into 16 bits)
        #reopen the modbus using the new baud rate
        self.mod.close()
        self.mod = ModbusSerialClient(port=self.port, baudrate=self.baudRate, framer=FramerType.RTU)

    def setSamplesPerFrame(self, numSamples):
        # set the period of the stream timer in microseconds
        self.samplesPerFrame = numSamples
        self.mod.write_register(13, numSamples)

    def readTemperature(self):
        self.mod.write_register(1, 0x20)
        rr = self.mod.read_holding_registers(address=3, count=1)
        lowByte = rr.registers[0]
        self.mod.write_register(1, 0x21)
        rr = self.mod.read_holding_registers(address=3, count=1)
        highByte = rr.registers[0]
        temperature = (highByte << 8) + lowByte
        temperature = twos_comp(temperature, 16)
        #The output of the temperature sensor is 0 LSB (typ.) at 25 °C.
        #Output resolution is 256LSB per degree C
        return (25 + (temperature / 256))   #convert to degrees C

    def readUniqueId(self):
        rr = self.mod.read_holding_registers(address=122, count=6)
        uniqueId = (rr.registers[0] << 80) + (rr.registers[1] << 64) + (rr.registers[2] << 48)  + (rr.registers[3] << 32) + (rr.registers[4] << 16) + (rr.registers[5] << 0)

        return uniqueId

    def tasks(self):
        if self.connect and self.stream:
            if (self.ser.inWaiting() > 0):
                self.sentence += self.ser.read(1024)
                if self.sentence.find(b'\x55\xAA') < 0: return

                vals = self.sentence.split(b'\x55\xAA')
                for i in range(len(vals) - 1):
                    val = vals[i]
                    print(val.hex())
                    if len(val) > 0:
                        for sampleIndex in range(0, self.samplesPerFrame):
                            self.gyro = np.roll(self.gyro, 1)
                            offset = sampleIndex * 12
                            self.gyro[0, 0] = twos_comp(int.from_bytes(val[offset:offset + 2], byteorder='little'),16)
                            self.gyro[1, 0] = twos_comp(int.from_bytes(val[offset + 2:offset + 4], byteorder='little'),16)
                            self.gyro[2, 0] = twos_comp(int.from_bytes(val[offset + 4:offset + 6], byteorder='little'),16)
                            self.acc = np.roll(self.acc, 1)
                            self.acc[0, 0] = twos_comp(int.from_bytes(val[offset + 6:offset + 8], byteorder='little'),16)
                            self.acc[1, 0] = twos_comp(int.from_bytes(val[offset + 8:offset + 10], byteorder='little'),16)
                            self.acc[2, 0] = twos_comp(int.from_bytes(val[offset + 10:offset + 12], byteorder='little'),16)
                        offset += 12
                        self.temp = twos_comp(int.from_bytes(val[offset: offset + 2], byteorder='little'),16)
                        self.temp = (25 + (self.temp / 256))
                        newFrameCounter = int.from_bytes(val[offset + 2: offset + 3], byteorder='little')

                        if(newFrameCounter != self.frameCounter):
                            print("Dropped Frame:" + str(self.frameCounter) + "," + str(newFrameCounter))
                        self.frameCounter = newFrameCounter + 1     #the next time around, newFrameCounter will be incremented by 1
                        if self.frameCounter > 255:
                            self.frameCounter = 0
                        self.CRC = int.from_bytes(val[offset + 3:offset + 5], byteorder='little')

                        # for index in range(0, len(val) - 1):
                        #     self.raw[index] = int.from_bytes(val[index:index+1],byteorder='little')

                self.sentence = vals[-1]

