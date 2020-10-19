#!/usr/bin/env python3
import paho.mqtt.client as paho
import random

broker="192.168.2.44"
port=1883

def on_publish(client,userdata,result):             #create function for callback
    print("data published \n")
    pass

client1= paho.Client("control1")                           #create client object
client1.on_publish = on_publish                          #assign function to callback
client1.connect(broker,port)                                 #establish connection
ret = client1.publish("power/line1",random.randint(0,9))    
