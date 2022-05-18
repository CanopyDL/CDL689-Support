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
        self.CRC = 0
        self.frameCounter = 0;
        self.temp = 0
        self.port = ''
        self.raw = np.zeros(self.buffer_length, dtype=np.int)
        self.baudRate = 9600
        self.samplesPerFrame = 1

    def open(self,port):
        self.port = port
        self.mod = ModbusSerialClient(port=port, baudrate=self.baudRate, method="RTU")
        self.connect=1
        self.mod.write_register(10, 0x96, unit=UNIT)  # stop streaming
        self.mod.write_register(10, 0x96, unit=UNIT)  # stop streaming
        self.mod.write_register(10, 0x96, unit=UNIT)  # stop streaming

        self.mod.write_register(1, 0x0F, unit=UNIT)  # WHO AM I
        self.mod.read_holding_registers(3, 1, unit=UNIT)
        #print(rr.registers[0])

        # setup accelerometer
        self.mod.write_register(3, 0x50, unit=UNIT)  # data
        self.mod.write_register(2, 0x10, unit=UNIT)  # IMU register

        # setup gyro
        self.mod.write_register(3, 0x50, unit=UNIT)  # data
        self.mod.write_register(2, 0x11, unit=UNIT)  # IMU register

    def close(self):
        self.connect = 0
        #self.ser.close()
        self.mod.close()

    def start_stream(self):
        self.mod.write_register(10, 0x69, unit=UNIT)  # start streaming
        self.stream = 1
        #switch from ModBus to Serial
        self.mod.close()
        self.ser = serial.Serial(self.port, self.baudRate, timeout=0)

    def stop_stream(self):
        self.ser.close()
        self.mod = ModbusSerialClient(port=self.port, baudrate=self.baudRate, method="RTU")
        self.mod.write_register(10, 0x96, unit=UNIT)  # stop streaming
        self.mod.write_register(10, 0x96, unit=UNIT)  # stop streaming
        self.mod.write_register(10, 0x96, unit=UNIT)  # stop streaming
        self.mod.write_register(10, 0x96, unit=UNIT)  # stop streaming
        self.mod.write_register(10, 0x96, unit=UNIT)  # stop streaming
        self.stream = 0

    def setUpdateRate(self, newRate):
        #set the period of the stream timer in microseconds
        self.mod.write_register(11, newRate, unit=UNIT)  # start streaming

    def setBaudRate(self, newRate):
        # set the period of the stream timer in microseconds
        self.baudRate = newRate
        self.mod.write_register(12, int(newRate / 100), unit=UNIT)  # set baudrate (divide by 100 to fit into 16 bits)
        #reopen the modbus using the new baud rate
        self.mod.close()
        self.mod = ModbusSerialClient(port=self.port, baudrate=self.baudRate, method="RTU")

    def setSamplesPerFrame(self, numSamples):
        # set the period of the stream timer in microseconds
        self.samplesPerFrame = numSamples
        self.mod.write_register(13, numSamples,
                                unit=UNIT)  # set baudrate (divide by 100 to fit into 16 bits)

    def readTemperature(self):
        self.mod.write_register(1, 0x20, unit=UNIT)
        rr = self.mod.read_holding_registers(3, 1, unit=UNIT)
        lowByte = rr.registers[0]
        self.mod.write_register(1, 0x21, unit=UNIT)
        rr = self.mod.read_holding_registers(3, 1, unit=UNIT)
        highByte = rr.registers[0]
        temperature = (highByte << 8) + lowByte
        temperature = twos_comp(temperature, 16)
        #The output of the temperature sensor is 0 LSB (typ.) at 25 °C.
        #Output resolution is 256LSB per degree C
        return (25 + (temperature / 256))   #convert to degrees C

    def readUniqueId(self):
        rr = self.mod.read_holding_registers(122, 6, unit=UNIT)
        uniqueId = (rr.registers[0] << 80) + (rr.registers[1] << 64) + (rr.registers[2] << 48)  + (rr.registers[3] << 32) + (rr.registers[4] << 16) + (rr.registers[5] << 0)

        return uniqueId

    def tasks(self):
        if self.connect and self.stream:
            if (self.ser.inWaiting() > 0):
                self.sentence += self.ser.read(50)
                vals = self.sentence.split(b'\x55\xAA')
                for i in range(len(vals) - 1):
                    val = vals[i]
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

                        self.temp = twos_comp(int.from_bytes(val[12:14], byteorder='little'),16)
                        self.temp = (25 + (self.temp / 256))

                        self.frameCounter = int.from_bytes(val[14:18], byteorder='little')

                        self.CRC = int.from_bytes(val[18:20], byteorder='little')

                        # for index in range(0, len(val) - 1):
                        #     self.raw[index] = int.from_bytes(val[index:index+1],byteorder='little')

                self.sentence = vals[-1]

