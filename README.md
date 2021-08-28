# Paradox Spectra 1738 Serial to MQTT

This Python script was made to run on Raspberry Pi B+ connected to the serial port of the Paradox Spectra 1738 alarm panel.

## Running with docker
* Set the IP address or hostname of your MQTT broker in the file config.yaml
* Build the image  
`docker build -t paradox2mqtt .`
* Run the container  
`docker run -d --device /dev/ttyAMA0:/dev/ttyAMA0 --restart=unless-stopped paradox2mqtt`  
  
config.yaml can be mounted to /usr/src/app/config.yaml at the run command (`-v $(pwd)/config.yaml:/usr/src/app/config.yaml`) to apply a modified configuration without rebuilding the image.
