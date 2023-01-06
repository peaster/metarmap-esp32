# Smart METARMap
A MQTT-Enabled METARMap that neatly fits into [Home Assistant](https://www.home-assistant.io/), [OpenHab](https://www.openhab.org/), and other custom MQTT ecosystems. This allows users to control this map using their smart home setups and expose it to voice assistants.

This project extends the functionality of [https://github.com/prueker/METARMap](https://github.com/prueker/METARMap) and the [original 
READMEs](https://github.com/prueker/METARMap/blob/63b50e9ffea9607dcefa397a4d2d52b58c17648a/README.md) contain full instructions on setup and hardware. The two projects differ at the software setup.

## Map Setup
* Install [Raspberry Pi OS Lite](https://www.raspberrypi.org/software/) on SD card
* [Enable Wi-Fi and SSH](https://medium.com/@danidudas/install-raspbian-jessie-lite-and-setup-wi-fi-without-access-to-command-line-or-using-the-network-97f065af722e)
* Install SD card and power up Raspberry Pi
* SSH (using [Putty](https://www.putty.org) or some other SSH tool) into the Raspberry and configure password and timezones
	* `passwd`
	* `sudo raspi-config`
* Update packages 
	* `sudo apt-get update`
	* `sudo apt-get upgrade`
* Copy the **[metarmap.py](metarmap.py)** and **[airports](airports)** files into the pi home directory (/home/pi)
* Install python3 and pip3 if not already installed
	* `sudo apt-get install python3`
	* `sudo apt-get install python3-pip`
* Install required python libraries for the project
	* [Neopixel](https://learn.adafruit.com/neopixels-on-raspberry-pi/python-usage): `sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel`
	* [Paho MQTT](https://www.eclipse.org/paho/index.php?page=clients/python/index.php): `sudo pip3 install paho-mqtt`
* Attach WS8211 LEDs to Raspberry Pi, if you are using just a few, you can connect the directly, otherwise you may need to also attach external power to the LEDs. For my purpose with 22 powered LEDs it was fine to just connect it directly. You can find [more details about wiring here](https://learn.adafruit.com/neopixels-on-raspberry-pi/raspberry-pi-wiring).

## Configure MQTT settings
Configuration is managed through a private `mqtt_config.py` file. This contains information about your MQTT broker, so it should never be checked into git. The file should be the following:

	broker_url = <broker_url>
	broker_port = <broker_port>
	set_topic = "home/metarmap/set"
	state_topic = "home/metarmap/state"
	broker_username = "admin"
	broker_password = "notrealpass"
		

To run the client permanently and to ensure it starts when you apply power to the Raspberry Pi, set up a service:

`sudo vim /etc/systemd/system/mqtt-client.service`
```
[Unit]
Description=mqtt client service

[Service]
ExecStart=python3 mqtt-service.py
WorkingDirectory=/home/pi/
Restart=always
RestartSec=10
User=pi

[Install]
WantedBy=multi-user.target 
```
And then enable it
```
sudo systemctl enable mqtt-client.service
sudo systemctl start mqtt-client.service
```

## Optional Map Configurations
### **Additional Wind condition blinking/fading functionality**
I recently expanded the script to also take wind condition into account and if the wind exceeds a certain threshold, or if it is gusting, make the LED for that airport either blink on/off or to fade between  two shades of the current flight category color.

If you want to use this extra functionality, then inside the **[metarmap.py](metarmap.py)** file set the **`ACTIVATE_WINDCONDITION_ANIMATION`** parameter to **True**.
* There are a few additional parameters in the script you can configure to your liking:
	* `FADE_INSTEAD_OF_BLINK` - set this to either **True** or **False** to switch between fading or blinking for the LEDs when conditions are windy
	* `WIND_BLINK_THRESHOLD` - in Knots for normal wind speeds currently at the airport
	* `ALWAYS_BLINK_FOR_GUSTS` - If you always want the blinking/fading to happen for gusts, regardless of the wind speed
	* `BLINKS_SPEED` - How fast the blinking happens, I found 1 second to be a happy medium so it's not too busy, but you can also make it faster, for example every half a second by using 0.5
	* `BLINK_TOTALTIME_SECONDS` = How long do you want the script to run. I have this set to 300 seconds as I have my crontab setup to re-run the script every 5 minutes to get the latest weather information
	
### **Additional Lightning in the vicinity blinking functionality**

After the recent addition for wind condition animation, I got another request from someone if I could add a white blinking animation to represent lightning in the area.
Please note that due to the nature of the METAR system, this means that the METAR for this airport reports that there is Lightning somewhere in the vicinity of the airport, but not necessarily right at the airport.

If you want to use this extra functionality, then inside the **[metarmap.py](metarmap.py)** file set the **`ACTIVATE_LIGHTNING_ANIMATION`** parameter to **True**.
* This shares two configuration parameters together with the wind animation that you can modify as you like:
	* `BLINKS_SPEED` - How fast the blinking happens, I found 1 second to be a happy medium so it's not too busy, but you can also make it faster, for example every half a second by using 0.5
	* `BLINK_TOTALTIME_SECONDS` = How long do you want the script to run. I have this set to 300 seconds as I have my crontab setup to re-run the script every 5 minutes to get the latest weather information