import paho.mqtt.client as mqtt
import time
import datetime
import logging
import broadlink
from daikin.daikin import utils
from daikin.daikin import (
    Daikin, DaikinMessage, Power, FanSpeed
)


MQTT_SERVER = "192.168.0.10"
MQTT_USER = ''
MQTT_PASSWORD = ''

BROADLINK_HOST = "192.168.0.12"
BROADLINK_MAC = bytearray(b'G\xe5\xb24\xea4')
BROADLINK_DEVICE_TYPE = 0x2737

TOPIC_AVAILABLE = "broadlink/available"
TOPIC_TEMPERATURE = "daikin/temperature"
TOPIC_POWER = "daikin/power"

daikin_message = DaikinMessage()


def on_connect(client, userdata, flags, rc):
    logging.info("Connected with result code {}".format(rc))
    client.publish(TOPIC_AVAILABLE, "true", retain=True)
    client.subscribe(TOPIC_POWER)
    client.subscribe(TOPIC_TEMPERATURE)

def on_message(client, userdata, msg):
    now = datetime.datetime.now()
    logging.info(" {} {} {}".format(
        now.strftime("%Y-%m-%d %H:%M:%S.%f"), msg.topic, msg.payload)
    )
    if msg.topic == TOPIC_POWER:
        if msg.payload in (b"true", "true"):
            print("ON")
            daikin_message.power = Power.ON
        else:
            print("OFF")
            daikin_message.power = Power.OFF
    if msg.topic == TOPIC_TEMPERATURE:
        daikin_message.temperature = int(msg.payload)

    daikin_message.recreate_blocks()
    logging.info("mensaje <{}>".format(daikin_message))
    client = Daikin()
    durations = client.message_to_durations(daikin_message)
    bl = utils.durations_to_broadlink(durations)
    dev = broadlink.gendevice(BROADLINK_DEVICE_TYPE,
                              (BROADLINK_HOST, 80),
                              BROADLINK_MAC)
    dev.auth()
    dev.send_data(bl)
    


if __name__ == '__main__':
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(level=logging.INFO, format = FORMAT)
    logging.info("starting")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.will_set(TOPIC_AVAILABLE, "false", retain=True)
    client.connect(MQTT_SERVER)
    client.loop_forever()
    


