import logging
import serial
from datetime import datetime
from struct import unpack
import paho.mqtt.client as mqtt


# Parses the 32-bit message from Paradox P1738 Serial Output
#  0                   1                   2                   3
#  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |     |T| E | |  Zone   |       |  Hours  |   Minutes   |       |
# +-------------------------------+-------------------------------+
def parse_msg(bytes):
    raw = unpack("!HH", bytes)
    type = (raw[0] >> 12) & 1
    event = (raw[0] >> 10) & 0b11
    zone = (raw[0] >> 4) & 0b11111
    hours = (raw[1] >> 11) & 0b11111
    minutes = (raw[1] >> 4) & 0b111111
    return type, event, zone

hostname = "localhost"

def get_topic_for_zone(zone):
    topics = {
        1: "p1738/zones/1",
        2: "p1738/zones/2",
        3: "p1738/zones/3",
        4: "p1738/zones/4",
        5: "p1738/zones/5",
        6: "p1738/zones/6",
        7: "p1738/zones/7",
        8: "p1738/zones/8",
    }
    return topics.get(zone, "p1738/unknown")

def get_state_for_event(event):
    states = {
        0: "CLOSED",
        1: "OPEN",
    }
    return states.get(event, "unknown")

def log_msg_bytes(bytes):
    raw = unpack("BBBB", bytes)
    text = hex(raw[0]) + " " + hex(raw[1]) + " " + hex(raw[2]) + " " + hex(raw[3])
    mqttc.publish("p1738/debug", payload=text, qos=1)
    logging.info(text)

logging.basicConfig(filename='p1738.log',level=logging.DEBUG)
logging.info("Connecting to MQTT Broker: " + hostname)

mqttc = mqtt.Client()
mqttc.will_set("p1738/service", payload="offline", qos=1, retain=True)
mqttc.connect(hostname)
mqttc.loop_start()

mqttc.publish("p1738/service", payload="online", qos=1, retain=True)

port = serial.Serial("/dev/ttyAMA0", baudrate=9600, inter_byte_timeout=1)

print("Paradox Spectra 1738 to MQTT started")

while True:
    rcv = port.read(4)
    if len(rcv) == 4:
        log_msg_bytes(rcv)
        (type, event, zone) = parse_msg(rcv)
        if (type == 0 and (event == 0 or event == 1) and (zone >= 0 and zone <= 8)):
            topic = get_topic_for_zone(zone)
            state = get_state_for_event(event)
            mqttc.publish(topic, payload=state, qos=1)        
            logging.info(state + " is being published to " + topic)
        else:
            logging.info("msg not recognized.")
    else:
        logging.info(repr(len(rcv)) + " bytes discarded")
