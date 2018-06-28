"""
http://rdlab.cdmt.vn/project-2013/daikin-ir-protocol
http://www.mcmajan.com/mcmajanwpr/blog/2013/10/21/ir-daikin-decodificare-protocolli-infrarossi-complessi/
https://github.com/blafois/Daikin-IR-Reverse
https://github.com/mjg59/python-broadlink
"""

import logging
import binascii
import time
from enum import Enum

from . import utils

def calculate_checksum(bs):
    total = 0
    for idx, b in enumerate(bs):
        total += b
    return total & 0xFF

class Power(Enum):
    ON = 1
    OFF = 0

class Mode(Enum):
    AUTO = 0
    DRY = 2
    COOL = 3
    HEAT = 4
    FAN = 6

class FanSpeed(Enum):
    AUTO = 10
    NIGHT = 11
    SPEED_1 = 3
    SPEED_2 = 4
    SPEED_3 = 5
    SPEED_4 = 6
    SPEED_5 = 7
    
class DaikinMessage():

    #I think this block is always fixed, but I am not sure, specially about block0[6]&0x08
    INITIAL_BLOCK0 = [0x11, 0xda, 0x27, 0x00, 0xc5, 0x10, 0x00, 0xe7] 
    
    INITIAL_BLOCK1 = [0x11, 0xda, 0x27, 0x00, 0x42,
                      0xfc, 0x24, #maybe time??
                      0x74] #checksum

    INITIAL_BLOCK2 = [0x11, 0xda, 0x27, 0x00, 0x00] #initial part of block
    
    def __init__(self):
        self.block0 = None
        self.block1 = None
        self.block2 = None

        self.power = Power.ON
        self.timer_on = False
        self.timer_on_duration = 0
        self.timer_off = False
        self.timer_off_duration = 0
        self.mode = Mode.COOL
        self.temperature = 24
        self.vertical_swing = False
        self.fan_speed = FanSpeed.AUTO
        self.horizontal_swing = False
        self.silent = True
        self.powerful = False
        self.sensor = True
        self.econo = False

    @staticmethod
    def from_block_bytes(block0, block1, block2):
        message = DaikinMessage()
        message.parse_block0(block0)
        message.parse_block1(block1)
        message.parse_block2(block2)
        return message

    def calculate_checksum(self, bs):
        total = 0
        for idx, b in enumerate(bs):
            total += b
            #print("total: ", total)
        return total & 0xFF
    

    def parse_block0(self, block0):
        if block0 != DaikinMessage.INITIAL_BLOCK0:
            raise Exception("wrong initial block. expected {} actual {}".format(DaikinMessage.INITIAL_BLOCK0,
                                                                                block0))
        self.block0 = block0

    def parse_block1(self, block1):
        self.block1 = block1
        #the only thing I can do is check checksum until I know what this is...
        if calculate_checksum(self.block1[0:7]) != self.block1[7]:
            raise Exception("wrong checksum in block 1")
        

    def parse_block2(self, block2):
        self.block2 = block2
        if calculate_checksum(self.block2[0:18]) != self.block2[18]:
            raise Exception("wrong checksum in block 2")
        if self.block2[0:5] != self.INITIAL_BLOCK2:
            raise Exception("initial bytes wrong in block 2. actual {} expected {}".
                            format(self.block2[0:5], self.INITIAL_BLOCK2, ))
        index = 0x05
        self.power = Power(self.block2[index] & 0x01)
        self.timer_on = (self.block2[index] & 0x02)
        self.timer_off = (self.block2[index] & 0x04)
        (self.block2[index] & 0x08) #I have seen 1
        self.mode = Mode(self.block2[index] >> 4 & 0x07)
        index = 0x06
        self.temperature = self.block2[index] >> 1 & 0x3F
        index = 0x07
        if self.block2[index] != 0x00:
            raise Exception("wrong byte index {} in block2".format(index))
        index = 0x08
        self.vertical_swing = (self.block2[index] & 0x0F) > 0
        self.fan_speed = FanSpeed((self.block2[index] >> 4) & 0x0F)
        index = 0x09
        self.horizontal_swing = (self.block2[index] & 0x0F) > 0
        #this is probably wrong
        self.timer_on_duration = (((self.block2[0x0B] & 0x07) << 8 ) + self.block2[0x0A]) / 60;
        #this is probably wrong
        self.timer_off_duration = (((self.block2[0x0C] & 0x7F) << 4 ) + ((self.block2[0x0B] >> 4) & 0x0F)) / 60;
        index = 0x0D
        self.powerful = self.block2[index] & 0x01 > 0
        self.silent = self.block2[index] & 0x20 > 0
        index = 0x0E
        if self.block2[index] != 0x00:
            raise Exception("wrong byte index {} in block2".format(index))
        index = 0x0F
        #I don't know what this means
        if self.block2[index] != 0xC1: 
            raise Exception("wrong byte {} index {} in block2".format(hex(self.block2[index]), index))
        index = 0X10
        self.sensor = self.block2[index] & 0x02 > 0
        self.econo = self.block2[index] & 0x04 > 0
        index = 0X11
        if self.block2[index] != 0x00:
            raise Exception("wrong byte index {} in block2".format(index))

    def recreate_block0(self):
        self.block0 = DaikinMessage.INITIAL_BLOCK0[:]

    def recreate_block1(self):
        self.block1 = DaikinMessage.INITIAL_BLOCK1[:]

    def recreate_block2(self):
        self.block2 = DaikinMessage.INITIAL_BLOCK2[:]
        #from now on the real message
        #index = 0x05
        if self.timer_on or self.timer_off:
            raise Exception("timers not implemented")
        value = self.power.value | 0x08 | (self.mode.value << 4)
        self.block2.append(value)
        #index = 0x06
        value = self.temperature << 1
        self.block2.append(value)
        #index = 0x07
        self.block2.append(0x00)
        #index = 0x08
        value = (0x0F if self.vertical_swing else 0x00) | (self.fan_speed.value << 4)
        self.block2.append(value)
        #index = 0x09
        value = 0x0F if self.horizontal_swing else 0x00
        self.block2.append(value)
        #index 0x0a, 0x0b y 0x0c. the timers' values. I put what I saw in one message...
        self.block2.append(0x00) #0x00
        self.block2.append(0x06) #0x00
        self.block2.append(0x60) #0x00
        #index = 0x0D
        value = self.powerful | self.silent << 5
        self.block2.append(value)
        #index = 0x0E
        self.block2.append(0x00)
        #index = 0x0F
        self.block2.append(0xC1)
        #index = 0x10
        value = 0x80 | self.sensor << 1 | self.econo << 2
        self.block2.append(value)
        #index = 0x11
        self.block2.append(0x00)
        self.block2.append(self.calculate_checksum(self.block2[0:18]))
        
    def recreate_blocks(self):
        self.recreate_block0()
        self.recreate_block1()
        self.recreate_block2()
        
    def as_bytes(self):
        if not self.block0:
            return None

        return "{} {} {}".format(
            utils.format_hex(self.block0),
            utils.format_hex(self.block1),
            utils.format_hex(self.block2),
            )

    def as_reversed_bits(self):
        if not self.block0:
            return None
        
        block0 = [format(int('{:08b}'.format(x)[::-1], 2), 'b').zfill(8) for x in self.block0]
        block1 = [format(int('{:08b}'.format(x)[::-1], 2), 'b').zfill(8) for x in self.block1]
        block2 = [format(int('{:08b}'.format(x)[::-1], 2), 'b').zfill(8) for x in self.block2]
        return (' '.join(block0) + " - " + ' '.join(block1) + " - " + ' '.join(block2))
    
    def __str__(self):
        resp = "{}\n{}".format(self.as_bytes(),
                              self.as_reversed_bits())
        resp += "\nPower: {}".format(self.power)
        resp += "\nTimer On: {}".format(self.timer_on)
        resp += "\nTimer Off: {}".format(self.timer_off)
        resp += "\nMode: {}".format(self.mode)
        resp += "\nTemperature: {}".format(self.temperature)
        resp += "\nFan Speed: {}".format(self.fan_speed)
        resp += "\nVertical Swing: {}".format(self.vertical_swing)
        resp += "\nHorizontal Swing: {}".format(self.horizontal_swing)
        resp += "\nTimer On Duration: {}".format(self.timer_on_duration)
        resp += "\nTimer Off Duration: {}".format(self.timer_off_duration)
        resp += "\nPowerful: {}".format(self.powerful)        
        resp += "\nSilent: {}".format(self.silent)
        resp += "\nSensor: {}".format(self.sensor)
        resp += "\nEcono: {}".format(self.econo)
        return resp

class Daikin():
    PULSE_LENGTH = (522, 350, 600)
    SPACE_ONE_LENGTH = (1400, 1200, 1500)
    SPACE_ZERO_LENGTH = (420, 350, 600)
    SPACE_POST_LONG_PULSE_LENGTH = (1770, 1600, 2000)
    PULSE_LONG_LENGTH = (3490, 3000, 4000)
    SPACE_LONG_LENGTH = (26800, 20000, 28000)
    SPACE_HUGE_LENGTH = (37150, 32000, 40000)
    SPACE_END = (200000,)

    def is_duration(self, duration, mark_type):
        if mark_type[1] < duration < mark_type[2]:
            return True
        return False

    def get_duration(self, mark_type):
        return mark_type[0]
    
    def __init__(self):
        pass


    def test_mark_expected(self, durations, index, mark):
        if not self.is_duration(durations[index], mark):
            raise Exception("wrong duration in position {}".format(index))
        return index + 1

    def parse_byte_duration(self, durations, index):
        result = 0
        for i in range(0,8):
            if self.is_duration(durations[index], Daikin.SPACE_ONE_LENGTH):
                result = result | (1 << i)
            elif self.is_duration(durations[index], Daikin.SPACE_ZERO_LENGTH):
                result = result | (0 << i)
            else:
                raise Exception("wrong duration parsing byte in position {}".format(index))
            index = index + 1
            index = self.test_mark_expected(durations, index, Daikin.PULSE_LENGTH)
        
        return index, result
        
    def get_message_from_durations(self, durations):
        index = 0
        #starts with five zeros
        index = self.test_mark_expected(durations, index, Daikin.PULSE_LENGTH)
        for i in range(0,5):
            index = self.test_mark_expected(durations, index, Daikin.SPACE_ZERO_LENGTH)
            index = self.test_mark_expected(durations, index, Daikin.PULSE_LENGTH)

        index = self.test_mark_expected(durations, index, Daikin.SPACE_LONG_LENGTH)
        index = self.test_mark_expected(durations, index, Daikin.PULSE_LONG_LENGTH)
        index = self.test_mark_expected(durations, index, Daikin.SPACE_POST_LONG_PULSE_LENGTH)
        index = self.test_mark_expected(durations, index, Daikin.PULSE_LENGTH)

        block0 = []
        for i in range(0,8):
            index, bt = self.parse_byte_duration(durations, index)
            block0.append(bt)

        index = self.test_mark_expected(durations, index, Daikin.SPACE_HUGE_LENGTH)
        index = self.test_mark_expected(durations, index, Daikin.PULSE_LONG_LENGTH)
        index = self.test_mark_expected(durations, index, Daikin.SPACE_POST_LONG_PULSE_LENGTH)
        index = self.test_mark_expected(durations, index, Daikin.PULSE_LENGTH)

        block1 = []
        for i in range(0,8):
            index, bt = self.parse_byte_duration(durations, index)
            block1.append(bt)

        index = self.test_mark_expected(durations, index, Daikin.SPACE_HUGE_LENGTH)
        index = self.test_mark_expected(durations, index, Daikin.PULSE_LONG_LENGTH)
        index = self.test_mark_expected(durations, index, Daikin.SPACE_POST_LONG_PULSE_LENGTH)
        index = self.test_mark_expected(durations, index, Daikin.PULSE_LENGTH)

        block2 = []
        for i in range(0,19):
            index, bt = self.parse_byte_duration(durations, index)
            block2.append(bt)

        return DaikinMessage.from_block_bytes(block0, block1, block2)

    def bytes_to_durations(self, bts):
        result = []
        for bt in bts:
            result += self.byte_to_durations(bt)
        return result

    def byte_to_durations(self, bt):
        result = []
        str_bits = ''.join(reversed(format(bt, 'b').zfill(8)))
        for b in str_bits:
            if b == '0':
                result.append(self.get_duration(Daikin.SPACE_ZERO_LENGTH))
            else:
                result.append(self.get_duration(Daikin.SPACE_ONE_LENGTH))
            result.append(self.get_duration(Daikin.PULSE_LENGTH))
        return result
        
    def message_to_durations(self, message):
        result = []
        result.append(self.get_duration(Daikin.PULSE_LENGTH))
        for i in range(0,5):
            result.append(self.get_duration(Daikin.SPACE_ZERO_LENGTH))
            result.append(self.get_duration(Daikin.PULSE_LENGTH))
        result.append(self.get_duration(Daikin.SPACE_LONG_LENGTH))
        result.append(self.get_duration(Daikin.PULSE_LONG_LENGTH))
        result.append(self.get_duration(Daikin.SPACE_POST_LONG_PULSE_LENGTH))
        result.append(self.get_duration(Daikin.PULSE_LENGTH))
        result += self.bytes_to_durations(message.block0)
        result.append(self.get_duration(Daikin.SPACE_HUGE_LENGTH))
        result.append(self.get_duration(Daikin.PULSE_LONG_LENGTH))
        result.append(self.get_duration(Daikin.SPACE_POST_LONG_PULSE_LENGTH))
        result.append(self.get_duration(Daikin.PULSE_LENGTH))
        result += self.bytes_to_durations(message.block1)
        result.append(self.get_duration(Daikin.SPACE_HUGE_LENGTH))
        result.append(self.get_duration(Daikin.PULSE_LONG_LENGTH))
        result.append(self.get_duration(Daikin.SPACE_POST_LONG_PULSE_LENGTH))
        result.append(self.get_duration(Daikin.PULSE_LENGTH))
        result += self.bytes_to_durations(message.block2)
        result.append(self.get_duration(Daikin.SPACE_END))
        return result
        
