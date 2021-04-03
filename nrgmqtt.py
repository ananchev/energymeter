import time

# Objects from Advanced Python Scheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# Pymodbus object
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

# Paho MQTT client publisher
import paho.mqtt.publish as publish

# Establish and configure logging facility
import logging
from logging.handlers import TimedRotatingFileHandler
fileHandler = TimedRotatingFileHandler('execution.log', when='midnight', backupCount=5)
fileFormatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s', '%Y-%m-%d %H:%M:%S')
fileHandler.setFormatter(fileFormatter)
logger = logging.getLogger('main')
logger.setLevel('INFO')
logger.addHandler(fileHandler)

# Cron expression defining meters read / mqttt publish time
SCHEDULER = '* * * * *' 

# IP and port of the Modbus TCP gateway
MODBUS_GW = dict(host='192.168.2.222', port=502)

# MQTT broker to publish data to
MQTT_BROKER = dict(hostname='192.168.2.8', port=1883, client_id='energy_meters')

# Energy meters definition
METERS = [
            dict(meter_id=2, mqtt_topic='energy/line2-total'),
            dict(meter_id=5, mqtt_topic='energy/line5-total')
         ]


class Scheduler():
    def __init__(self, job_callable):
        self.job_id = 'read_and_publish'
        self.scheduler = BlockingScheduler()
        self.scheduler.add_job(job_callable, 
                               trigger=CronTrigger.from_crontab(SCHEDULER),
                               id=self.job_id)
        self.scheduler.add_listener(self._listener, mask=EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.scheduler.start()

    def _listener(self, event):
        if event.exception:
            logger.info('Publish job execution failed. Please check logfile for details.')
        else:
            logger.info('Publish job was executed successfully.')
        logger.info('Next run is on {}.'.format(self.next_runtime))

    def shutdown(self):
        self.scheduler.shutdown()

    @property
    def next_runtime(self):
        job = self.scheduler.get_job('read_and_publish')
        return job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z')


class ReaderPublisher():
    def __init__(self):
        self.client = ModbusTcpClient(**MODBUS_GW)
        self.read_results = list()

    def _connect(self, retries = 0):
        connection = self.client.connect()
        if not connection:
            if (retries < 3):
                time.sleep(1)
                self._connect(self, retries+1) 
            else:
                raise Exception('cannot establish connection to gateway')
        logger.info('connected to Modbus gateway')

    def read_and_publish(self):
        self._connect()
        self.read_results.clear()
        for m in METERS:
            meter_id = m.get('meter_id')
            result = self._read(meter_id)
            decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big)
            energy_kwh = decoder.decode_32bit_uint() / 100
            pub_topic = m.get('mqtt_topic')
            logger.info(f"{pub_topic} = {energy_kwh} kWh")
            self.read_results.append(dict(topic=pub_topic, payload = energy_kwh))
        self.client.close()
        self._publish_to_mqtt()

    # retry in case of bad read operation (ModbusIOException) due to connection issues. 
    def _read(self, meter_id):
        result = self.client.read_holding_registers(address=0,count=2,unit=meter_id)
        if result.isError():
            logger.warn("invalid result, retrying the read operation...")
            result = self._read(meter_id)
        return result

    def _publish_to_mqtt(self):   
        res = publish.multiple(self.read_results, **MQTT_BROKER)

def run(reader_publisher : ReaderPublisher):
    print('running')
    reader_publisher.read_and_publish()
    logger.info('read data published')


if __name__ == '__main__':
    try:
        rp = ReaderPublisher()
        sh = Scheduler(lambda: run(rp))

    except (KeyboardInterrupt, SystemExit):
        exit()
