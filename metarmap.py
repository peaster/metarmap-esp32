#!/usr/bin/env python3
import urllib.request
import xml.etree.ElementTree as ET
import board
import neopixel
import time
import datetime

# ---------------------------------------------------------------------------
# ------------START OF CONFIGURATION-----------------------------------------
# ---------------------------------------------------------------------------

# NeoPixel LED Configuration
LED_COUNT = 50			# Number of LED pixels.

COLOR_VFR = (255, 0, 0)		# Green
COLOR_VFR_FADE = (75, 0, 0)		# Green Fade for wind
COLOR_MVFR = (0, 0, 255)		# Blue
COLOR_MVFR_FADE = (0, 0, 125)		# Blue Fade for wind
COLOR_IFR = (0, 255, 0)		# Red
COLOR_IFR_FADE = (0, 125, 0)		# Red Fade for wind
COLOR_LIFR = (0, 125, 125)		# Magenta
COLOR_LIFR_FADE = (0, 75, 75)		# Magenta Fade for wind
COLOR_CLEAR = (0, 0, 0)		# Clear
COLOR_LIGHTNING = (255, 255, 255)		# White

# ----- Blink/Fade functionality for Wind and Lightning -----
# Do you want the METARMap to be static to just show flight conditions, or do you also want blinking/fading based on current wind conditions
# Set this to False for Static or True for animated wind conditions
ACTIVATE_WINDCONDITION_ANIMATION = False
# Do you want the Map to Flash white for lightning in the area
# Set this to False for Static or True for animated Lightning
ACTIVATE_LIGHTNING_ANIMATION = False
# Fade instead of blink
FADE_INSTEAD_OF_BLINK = True			# Set to False if you want blinking
# Blinking Windspeed Threshold
WIND_BLINK_THRESHOLD = 18			# Knots of windspeed
# Always animate for Gusts (regardless of speeds)
ALWAYS_BLINK_FOR_GUSTS = False
# Blinking Speed in seconds
BLINK_SPEED = 1.0			# Float in seconds, e.g. 0.5 for half a second
# Total blinking time in seconds.
# For example set this to 300 to keep blinking for 5 minutes if you plan to run the script every 5 minutes to fetch the updated weather
BLINK_TOTALTIME_SECONDS = 300

# ---------------------------------------------------------------------------
# ------------END OF CONFIGURATION-------------------------------------------
# ---------------------------------------------------------------------------
class MetarMap:

	def __init__(self, brightness):
		self.airports = self.setAirports
		self.brightness = brightness

	def setAirports(self):
		# Read the airports file to retrieve list of airports and use as order for LEDs
		with open("/home/pi/airports") as f:
			airports = f.readlines()
		airports = [x.strip() for x in airports]
		return airports

	def shutdownLights(self):
		pixels = neopixel.NeoPixel(board.D18, LED_COUNT)
		pixels.deinit()		

	def updateLights(self):
		# Initialize the LED strip
		print("Wind animation:" + str(ACTIVATE_WINDCONDITION_ANIMATION))
		print("Lightning animation:" + str(ACTIVATE_LIGHTNING_ANIMATION))
		pixels = neopixel.NeoPixel(
			board.D18, LED_COUNT, brightness=self.brightness, pixel_order=neopixel.GRB, auto_write=False)

		# Retrieve METAR from aviationweather.gov data server
		# Details about parameters can be found here: https://www.aviationweather.gov/dataserver/example?datatype=metar
		url = "https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&hoursBeforeNow=5&mostRecentForEachStation=true&stationString=" + \
			",".join([item for item in self.airports() if item != "NULL"])
		print(url)
		req = urllib.request.Request(url, headers={
									'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 Edg/86.0.622.69'})
		content = urllib.request.urlopen(req).read()

		# Retrieve flying conditions from the service response and store in a dictionary for each airport
		root = ET.fromstring(content)
		conditionDict = {"NULL": {"flightCategory": "", "windDir": "", "windSpeed": 0, "windGustSpeed":  0, "windGust": False, "lightning": False,
			"tempC": 0, "dewpointC": 0, "vis": 0, "altimHg": 0, "obs": "", "skyConditions": {}, "obsTime": datetime.datetime.now()}}
		conditionDict.pop("NULL")

		# Build list of weather stations
		stationList = []
		for metar in root.iter('METAR'):
			stationId = metar.find('station_id').text
			if metar.find('flight_category') is None:
				print("Missing flight condition, skipping.")
				continue
			flightCategory = metar.find('flight_category').text
			windDir = ""
			windSpeed = 0
			windGustSpeed = 0
			windGust = False
			lightning = False
			tempC = 0
			dewpointC = 0
			vis = 0
			altimHg = 0.0
			obs = ""
			skyConditions = []
			if metar.find('wind_gust_kt') is not None:
				windGustSpeed = int(metar.find('wind_gust_kt').text)
				windGust = (True if (ALWAYS_BLINK_FOR_GUSTS or windGustSpeed >
							WIND_BLINK_THRESHOLD) else False)
			if metar.find('wind_speed_kt') is not None:
				windSpeed = int(metar.find('wind_speed_kt').text)
			if metar.find('wind_dir_degrees') is not None:
				windDir = metar.find('wind_dir_degrees').text
			if metar.find('temp_c') is not None:
				tempC = int(round(float(metar.find('temp_c').text)))
			if metar.find('dewpoint_c') is not None:
				dewpointC = int(round(float(metar.find('dewpoint_c').text)))
			if metar.find('visibility_statute_mi') is not None:
				vis = int(round(float(metar.find('visibility_statute_mi').text)))
			if metar.find('altim_in_hg') is not None:
				altimHg = float(round(float(metar.find('altim_in_hg').text), 2))
			if metar.find('wx_string') is not None:
				obs = metar.find('wx_string').text
			if metar.find('observation_time') is not None:
				obsTime = datetime.datetime.fromisoformat(
					metar.find('observation_time').text.replace("Z", "+00:00"))
			for skyIter in metar.iter("sky_condition"):
				skyCond = {"cover": skyIter.get("sky_cover"), "cloudBaseFt": int(
					skyIter.get("cloud_base_ft_agl", default=0))}
				skyConditions.append(skyCond)
			if metar.find('raw_text') is not None:
				rawText = metar.find('raw_text').text
				lightning = False if rawText.find('LTG') == -1 else True
			print(stationId + ":"
			+ flightCategory + ":"
			+ str(windDir) + "@" + str(windSpeed) +
				("G" + str(windGustSpeed) if windGust else "") + ":"
			+ str(vis) + "SM:"
			+ obs + ":"
			+ str(tempC) + "/"
			+ str(dewpointC) + ":"
			+ str(altimHg) + ":"
			+ str(lightning))
			conditionDict[stationId] = {"flightCategory": flightCategory, "windDir": windDir, "windSpeed": windSpeed, "windGustSpeed": windGustSpeed, "windGust": windGust,
				"vis": vis, "obs": obs, "tempC": tempC, "dewpointC": dewpointC, "altimHg": altimHg, "lightning": lightning, "skyConditions": skyConditions, "obsTime": obsTime}
			stationList.append(stationId)

		numAirports = len(stationList)
		# Iterate through airports and set pixels
		i = 0
		for airportcode in self.airports():
			# Skip NULL entries
			if airportcode == "NULL":
				i += 1
				continue

			color = COLOR_CLEAR
			conditions = conditionDict.get(airportcode, None)
			windy = False
			lightningConditions = False

			if conditions != None:
				if conditions["flightCategory"] == "VFR":
					color = COLOR_VFR
				elif conditions["flightCategory"] == "MVFR":
					color = COLOR_MVFR
				elif conditions["flightCategory"] == "IFR":
					color = COLOR_IFR
				elif conditions["flightCategory"] == "LIFR":
					color = COLOR_LIFR
				else:
					color = COLOR_CLEAR
			print("Setting LED " + str(i) + " for " + airportcode + " to " + ("lightning " if lightningConditions else "") +
					("windy " if windy else "") + (conditions["flightCategory"] if conditions != None else "None") + " " + str(color))
			pixels[i] = color
			i += 1

		# Update actual LEDs all at once
		pixels.show()
		print()
		print("Done")
