#!/usr/bin/python3

from time import sleep, time
import paho.mqtt.client as mqtt
from lights import Element
from config import *
import sys

from knx import Knx

knx = Knx()

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.

    client.subscribe("/switch/#")
    client.subscribe("/update/#")
    
    print("initialising states")
    for key in LIGHTS.keys():
        knx.getState(LIGHTS[key].groupAdress)
        knx.read()

    print("done initialising states")
    

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")

        print(msg.topic+" "+payload)
        split = msg.topic.split("/")[1:]

        element: Element = LIGHTS["/" + "/".join(split[1:])]


        if (split[0] == "update"):
            print("update: " + element.groupAdress)
            knx.getState(element.groupAdress)

        elif (split[0] == "switch"):
            print("switch: " + element.groupAdress + " " + payload)

            if (element.dimmable):
                if (int(payload) == 255):
                    knx.writeOn(element.secondAdress)
                elif (int(payload) == 0):
                    knx.writeOff(element.secondAdress)
                else:
                    knx.writeValueByte(element.groupAdress, int(payload))
                print("/" + "/".join(split[1:]), " : ", int(payload))
                client.publish("/" + "/".join(split[1:]), int(payload))
            elif (payload == "on"):
                knx.writeOn(element.groupAdress)
                print("/" + "/".join(split[1:]), " : ", payload)
                client.publish("/" + "/".join(split[1:]), payload)
            elif (payload == "off"):
                knx.writeOff(element.groupAdress)
                print("/" + "/".join(split[1:]), " : ", payload)
                client.publish("/" + "/".join(split[1:]), payload)


    except Exception as e:
        sys.exit("something went wrong: %s" % str(e))


client:mqtt.Client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(username=mqtt_username, password=mqtt_password)

connected = False
while(not connected):
    try:
        client.connect(mqtt_adress, mqtt_port, mqtt_keep_alive)
        connected = True
    except:
        connected = False
        sleep(5)
    

lightsKeyList = list(LIGHTS.keys())
lightsKeyLenght = len(lightsKeyList)
updateIndex = 0

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_start()



lastTime = time()
run =True

while(run):
    if ((time() - lastTime) > (generalUpadteFrequency / lightsKeyLenght)) and doGeneralUpdate:
        knx.getState(LIGHTS[lightsKeyList[updateIndex]].groupAdress)
        updateIndex += 1
        if updateIndex == lightsKeyLenght:
            updateIndex = 0
        lastTime = time()
    
    knx.write()
    knx.read()
    while not knx.readBuffer.empty():
        data = knx.readBuffer.get_nowait()
        if data[2] == 0:
            for key in LIGHTS.keys():
                if LIGHTS[key].groupAdress == data[1]:
                    client.publish(key, data[3])
                    break
                elif LIGHTS[key].secondAdress == data[1]:
                    if data[3] == "on":
                        client.publish(key, 255)
                    if data[3] == "off":
                        client.publish(key, 0)
                    break
        elif data[2] == 1:
            for key in LIGHTS.keys():
                if LIGHTS[key].groupAdress == data[1]:
                    client.publish(key, data[3])
                    break
        elif data[2] == 2:
            for key in LIGHTS.keys():
                if LIGHTS[key].groupAdress == data[1]:
                    client.publish(key, data[3])
                    break

client.loop_stop()