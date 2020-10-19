#!/usr/bin/env python
import paho.mqtt.client as paho
import random

broker="192.168.2.44"
port=1883

def on_publish(client,userdata,result):
    print("data published")
    pass

def pub(prev=0):
    client1= paho.Client("control1")
    client1.on_publish = on_publish
    client1.connect(broker,port)
    value = prev + random.randint(0,9)
    ret = client1.publish("meter/line1", value)
    return value    

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
def listener(event):
    if not event.exception:
        job = scheduler.get_job(event.job_id)
        if job.name == 'pub':
            ret = event.retval
            scheduler.modify_job(job.id, args=[ret])
        return 0


from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = BlockingScheduler()
scheduler.add_listener(listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
print(listener)
scheduler.add_job(pub, IntervalTrigger(seconds=3600))
try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    pass 