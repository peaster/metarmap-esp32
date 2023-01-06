import paho.mqtt.client as mqtt
import mqtt_config as config
import os
from metarmap import MetarMap

broker_url = config.broker_url
broker_port = config.broker_port
state = "OFF"

map = MetarMap(0.17)

def on_connect(client, userdata, flags, rc):
   print("Connected With Result Code: {}".format(rc))

def on_message(client, userdata, message):
    decodedMessage = message.payload.decode()
    print("Message received from broker: "+ decodedMessage)
    if decodedMessage == 'ON':
        map.updateLights()
        state = "ON"
    elif (decodedMessage == 'OFF') :
        map.shutdownLights()
        state = "OFF"

client = mqtt.Client('metarmap')
client.on_connect = on_connect
#To Process Every Other Message
client.on_message = on_message

if config.broker_username:
    client.username_pw_set(username=config.broker_username, password=config.broker_password)
client.connect(broker_url, broker_port)

client.subscribe(config.set_topic, qos=1)
client.publish(topic=config.state_topic, payload=state, qos=0, retain=True)

client.loop_forever()