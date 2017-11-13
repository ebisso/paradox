"""
P1738.py
This script listens for debug serial port packets from a Paradox 1738
alarm panel and sends the decoded messages to a MQTT broker.
"""
import logging
import sys
import struct
import serial
import paho.mqtt.client as mqtt
import yaml

# Notes on the Paradox P1738 Serial Output packets
# This info comes from looking at the different packets received on the serial
# port while performing different actions such as opening and closing each of
# the contacts, arming and disarming the panel, etc.
# This is incomplete and some parts may be wrong.
# Each packet has a length of 32-bit, where the first 2 bytes is the data of
# the event and the last 2 bytes is a timestamp.
#  0                   1                   2                   3
#  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |     |T| E | |  Zone   |       |  Hours  |   Minutes   |       |
# +-------------------------------+-------------------------------+

def parse_msg(packet):
    """ Decode a serial packet into a meaningful message """
    raw = struct.unpack("!HH", packet)
    type_ = (raw[0] >> 12) & 1
    event = (raw[0] >> 10) & 0b11
    zone = (raw[0] >> 4) & 0b11111
    hours = (raw[1] >> 11) & 0b11111
    minutes = (raw[1] >> 4) & 0b111111
    return type_, event, zone, hours, minutes

def get_topic_for_zone(zone):
    """ Maps a zone index to a MQTT topic """
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
    """ Maps an event value to a corresponding message """
    states = {
        0: "CLOSED",
        1: "OPEN",
    }
    return states.get(event, "unknown")

def log_msg_bytes(packet):
    """ Logs the packet content """
    raw = struct.unpack("BBBB", packet)
    text = hex(raw[0]) + " " + hex(raw[1]) + " " + hex(raw[2]) + " " + hex(raw[3])
    MQTT_CLIENT.publish("p1738/debug", payload=text, qos=1)
    logging.debug(text)

def run_loop():
    """
    The main loop listens for packets from the serial port and decodes them.
    If a message is recognized, it is published to a MQTT topic.
    """
    while True:
        # Read first byte
        rcv = SERIAL.read(1)
        if len(rcv) == 1:
            # Read the following 3 bytes
            rcv += SERIAL.read(3)
            if len(rcv) == 4:
                log_msg_bytes(rcv)
                (type_, event, zone, _hours, _minutes) = parse_msg(rcv)
                if type_ == 0 and (event == 0 or event == 1) and (zone >= 0 and zone <= 8):
                    topic = get_topic_for_zone(zone)
                    state = get_state_for_event(event)
                    MQTT_CLIENT.publish(topic, payload=state, qos=1)
                    logging.info(state + " is being published to " + topic)
            else:
                logging.warning(repr(len(rcv)) + " bytes discarded: " + repr(rcv))

LOGGING_FILE_HANDLER = logging.FileHandler('p1738.log', 'w')
LOGGING_FILE_HANDLER.setLevel(logging.WARNING)
LOGGING_STREAM_HANDLER = logging.StreamHandler(sys.stdout)
LOGGING_STREAM_HANDLER.setLevel(logging.INFO)
logging.getLogger().addHandler(LOGGING_FILE_HANDLER)
logging.getLogger().addHandler(LOGGING_STREAM_HANDLER)

# Read configuration
CONFIG = yaml.safe_load(open("1738.yaml"))

MQTT_BROKER = CONFIG['mqtt_broker']
logging.info("Connecting to MQTT Broker: " + MQTT_BROKER)

MQTT_CLIENT = mqtt.Client()
MQTT_CLIENT.will_set("p1738/service", payload="offline", qos=1, retain=True)
MQTT_CLIENT.connect(MQTT_BROKER)
MQTT_CLIENT.loop_start()

MQTT_CLIENT.publish("p1738/service", payload="online", qos=1, retain=True)

SERIAL = serial.Serial("/dev/ttyAMA0", baudrate=9600, timeout=5)

print("Paradox Spectra 1738 to MQTT started")
logging.info("Connected")

run_loop()
