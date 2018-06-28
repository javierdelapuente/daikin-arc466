"""
Some functions in this file are copy-pasted and slightly modified from 
https://github.com/mjg59/python-broadlink

The MIT License (MIT)

Copyright (c) 2014 Mike Ryan
Copyright (c) 2016 Matthew Garrett
Copyright (c) 2018 Matthew Garrett

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

TICK = 32.84
IR_TOKEN = 0x26

def format_hex(data):
    return ''.join(format(x, '02x') for x in bytearray(data))

def format_durations(data):
    result = ''
    for i in range(0, len(data)):
        if len(result) > 0:
            result += ' '
        result += ('+' if i % 2 == 0 else '-') + str(data[i])
    return result


def to_microseconds(bts):
    result = []
    #  print bytes[0] # 0x26 = 38for IR
    length = bts[2] + 256 * bts[3]  # presently ignored
    index = 4
    while index < len(bts):
        chunk = bts[index]
        index += 1
        if chunk == 0:
            chunk = bts[index]
            chunk = 256 * chunk + bts[index + 1]
            index += 2

        if chunk == 0x0d05 and index > length:
            break
        result.append(int(round(chunk*TICK)))
    return result

def durations_to_broadlink(durations):
    real_length = 3
    for dur in durations:
        real_length += 1
        num = int(round(dur / TICK))
        if num > 255:
            real_length += 2
    
    result = bytearray()
    result.append(IR_TOKEN)
    result.append(0)  # repeat
    result.append(real_length % 256)
    result.append(int(real_length / 256))
    for dur in durations:
        num = int(round(dur / TICK))
        if num > 255:
            result.append(0)
            result.append(int(num / 256))
        result.append(num % 256)
    result.append(0x00)        
    result.append(0x0d)
    result.append(0x05)
    return result
