"""
paradox2mqtt.py
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
    for mapping in message_mapping:
        if mapping['bytes'] == code:
            return mapping
    return None


def log_msg_bytes(packet):
    """ Logs the packet content """
    raw = struct.unpack("BBBB", packet)
    text = (hex(raw[0]) + " " + hex(raw[1]) + " " + hex(raw[2]) + " "
            + hex(raw[3]))
    mqtt_client.publish("paradox2mqtt/debug", payload=text, qos=1)
    logging.info("In: %s", text)


def run_loop():
    """
    The main loop listens for packets from the serial port and decodes them.
    If a message is recognized, it is published to a MQTT topic.
    """
    while True:
        # Read first byte
        rcv = _serial.read(1)
        if len(rcv) == 1:
            # Read the following 3 bytes
            rcv += _serial.read(3)
            if len(rcv) == 4:
                log_msg_bytes(rcv)
                (code, _hours, _minutes) = parse_msg(rcv)
                mapping = find_mapping(code)
                if mapping:
                    topic = mapping['topic']
                    message = mapping['message']
                    logging.info("Out: %s, %s", repr(topic), repr(message))
                    mqtt_client.publish(topic, payload=message, qos=1)
            else:
                logging.warning(
                    "The following bytes have been discarded: %s",
                    repr(rcv))


# Initialize logger to file and standard output
logging.getLogger().setLevel(logging.INFO)
logging_file_handler = logging.FileHandler('paradox2mqtt.log', 'w')
logging_file_handler.setLevel(logging.WARNING)
logging_stream_handler = logging.StreamHandler(sys.stdout)
logging_stream_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(logging_file_handler)
logging.getLogger().addHandler(logging_stream_handler)


logging.info("Reading configuration file")
with open("config.yaml", encoding='utf8') as f:
    config = yaml.safe_load(f)

mqtt_broker = config['mqtt_broker']
serial_device = config['serial_device']
status_topic = config['status']['topic']
status_message_connect = config['status']['message_connect']
status_message_disconnect = config['status']['message_disconnect']
message_mapping = config['message_mapping']

logging.info("Connecting to MQTT Broker: %s", mqtt_broker)

mqtt_client = mqtt.Client()
mqtt_client.will_set(status_topic, payload=status_message_disconnect, qos=1,
                    retain=True)
mqtt_client.connect(mqtt_broker)
mqtt_client.loop_start()

logging.info("Connected")
mqtt_client.publish(status_topic, payload=status_message_connect, qos=1,
                    retain=True)

logging.info("Opening serial device: %s", serial_device)
_serial = serial.Serial(serial_device, baudrate=9600, timeout=5)


logging.info("Started listening for packets")
run_loop()
