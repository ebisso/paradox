Paradox Spectra 1738 Serial to Home Assistant MQTT Integration

This Python script was made to run on Raspberry Pi B+ connected to the serial port of the Paradox Spectra 1738 alarm panel.

Usage:

docker build -t paradox .

docker run -d --network host --device /dev/ttyAMA0:/dev/ttyAMA0 --restart always paradox
