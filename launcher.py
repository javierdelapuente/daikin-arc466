from daikin.daikin import (
    Daikin, DaikinMessage, Power, FanSpeed
)
from daikin.daikin import utils
import broadlink
import time

client = Daikin()
message = DaikinMessage()
message.power = Power.ON
message.econo = True
message.fan_speed = FanSpeed.NIGHT
message.temperature = 23
message.recreate_blocks()

durations = client.message_to_durations(message)
bl = utils.durations_to_broadlink(durations)



host = '192.168.0.12'
mac = bytearray(b'G\xe5\xb24\xea4')
dev_type = 0x2737

dev = broadlink.gendevice(dev_type, (host, 80), mac)
dev.auth()

dev.send_data(bl)


