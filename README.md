# Paradox Spectra 1738 Serial to Home Assistant MQTT Integration

This Python script was made to run on Raspberry Pi B+ connected to the serial port of the Paradox Spectra 1738 alarm panel.

## With Docker

### Usage:

`docker build -t paradox .`

Here you may need to use your own tty device ( it may be ttyUSB0 )

`docker run -d --network host --device /dev/ttyAMA0:/dev/ttyAMA0 --restart always paradox`


## Without Docker

### Usage:

You may run this script using python3 with the required modules

Make sure you have python

`sudo apt install python3-pip`

Install the required modules

`pip3 install -r requirements.txt`

Launch the tool

`pip3 p1738.py`
