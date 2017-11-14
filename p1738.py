"""
P1738.py
This script listens for debug serial port packets from a Paradox Spectra 1738
alarm panel and sends decoded messages to a MQTT broker.
"""
import logging
import sys
import struct
import serial
import paho.mqtt.client as mqtt
import yaml

print("""
         ██╗███████╗██████╗  █████╗ 
        ███║╚════██║╚════██╗██╔══██╗
        ╚██║    ██╔╝ █████╔╝╚█████╔╝
         ██║   ██╔╝  ╚═══██╗██╔══██╗
         ██║   ██║  ██████╔╝╚█████╔╝
         ╚═╝   ╚═╝  ╚═════╝  ╚════╝
A MQTT bridge for Paradox Spectra alarm panel
""")

# Notes on the Paradox P1738 Serial Output packets
# This info comes from looking at the different packets received on the serial
# port while performing different actions such as opening and closing each of
# the contacts, arming and disarming the panel, etc.
# This is incomplete and some parts may be wrong.
# Each packet has a length of 32-bit, where the first group of 2 bytes is an
# event code and the last group of 2 bytes is a timestamp.
#  0                   1                   2                   3
#  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |     |T| E | |  Zone   |       |  Hours  | |  Minutes  |       |
# +-------------------------------+-------------------------------+

def parse_msg(packet):
    """ Decodes a serial packet into event code and timestamp parts """
    raw = struct.unpack("!BBH", packet)
    code = [raw[0], raw[1]]
    hours = (raw[2] >> 11) & 0b11111
    minutes = (raw[2] >> 4) & 0b111111
    return code, hours, minutes

def find_mapping(code):
    """ Looks-up an event code for a matching message mapping """
    for mapping in MESSAGE_MAPPING:
        if mapping['bytes'] == code:
            return mapping

def log_msg_bytes(packet):
    """ Logs the packet content """
    raw = struct.unpack("BBBB", packet)
    text = (hex(raw[0]) + " " + hex(raw[1]) + " " + hex(raw[2]) + " "
            + hex(raw[3]))
    MQTT_CLIENT.publish("p1738/debug", payload=text, qos=1)
    logging.info("In: " + text)

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
                (code, _hours, _minutes) = parse_msg(rcv)
                mapping = find_mapping(code)
                if mapping:
                    topic = mapping['topic']
                    message = mapping['message']
                    logging.info("Out: " + repr(topic) + ", " + repr(message))
                    MQTT_CLIENT.publish(topic, payload=message, qos=1)
            else:
                logging.warning("The following bytes have been discarded: " +
                                repr(rcv))

logging.getLogger().setLevel(logging.INFO)
LOGGING_FILE_HANDLER = logging.FileHandler('p1738.log', 'w')
LOGGING_FILE_HANDLER.setLevel(logging.WARNING)
LOGGING_STREAM_HANDLER = logging.StreamHandler(sys.stdout)
LOGGING_STREAM_HANDLER.setLevel(logging.INFO)
logging.getLogger().addHandler(LOGGING_FILE_HANDLER)
logging.getLogger().addHandler(LOGGING_STREAM_HANDLER)

# Read configuration
logging.info("Reading configuration file")
CONFIG = yaml.safe_load(open("1738.yaml"))

MQTT_BROKER = CONFIG['mqtt_broker']
SERIAL_DEVICE = CONFIG['serial_device']
STATUS_TOPIC = CONFIG['status']['topic']
STATUS_MESSAGE_CONNECT = CONFIG['status']['message_connect']
STATUS_MESSAGE_DISCONNECT = CONFIG['status']['message_disconnect']
MESSAGE_MAPPING = CONFIG['message_mapping']

logging.info("Connecting to MQTT Broker: " + MQTT_BROKER)

MQTT_CLIENT = mqtt.Client()
MQTT_CLIENT.will_set(STATUS_TOPIC, payload=STATUS_MESSAGE_DISCONNECT, qos=1,
                     retain=True)
MQTT_CLIENT.connect(MQTT_BROKER)
MQTT_CLIENT.loop_start()

MQTT_CLIENT.publish(STATUS_TOPIC, payload=STATUS_MESSAGE_CONNECT, qos=1,
                    retain=True)

logging.info("Connected")

logging.info("Opening serial device: " + SERIAL_DEVICE)
SERIAL = serial.Serial(SERIAL_DEVICE, baudrate=9600, timeout=5)

logging.info("Listening for packets")

run_loop()
