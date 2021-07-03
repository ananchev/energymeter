import time
from datetime import datetime, timezone

# Pymodbus object
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

# Paho MQTT client publisher
import paho.mqtt.publish as publish

# Python InfluxDB client
from influxdb import InfluxDBClient

# Establish and configure logging facility
import logging
from logging.handlers import TimedRotatingFileHandler
fileHandler = TimedRotatingFileHandler('/applog/application.log', when='midnight', backupCount=5)
fileFormatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s', '%Y-%m-%d %H:%M:%S')
fileHandler.setFormatter(fileFormatter)
logger = logging.getLogger('main')
logger.setLevel('INFO')
logger.addHandler(fileHandler)

# IP and port of the Modbus TCP gateway
MODBUS_GW = dict(host='192.168.2.222', port=502)

# MQTT broker to publish data to
MQTT_BROKER = dict(hostname='192.168.2.8', port=1883, client_id='energy_meters')

# InfluxDB connection parameters (where historical data is persisted)
INLUX_DB = dict(host='192.168.2.8', port=8086, username='ananchev', password='1Race96R', database='openhab')

# InfuxDB measurement names where total energy is stored (correspond to Openhab persisted)
INFLUX_TOTAL_ENRGY_MEASUREMENTS = "l2TotalEnergy|l5TotalEnergy"

# Energy meters definition
METERS = [
            dict(meter_id=2, 
                 mqtt_topic_total='energy/line2-total', 
                 mqtt_topic_last_hour='energy/line2-last-hour'),
            dict(meter_id=5, 
                 mqtt_topic_total='energy/line5-total', 
                 mqtt_topic_last_hour='energy/line5-last-hour')
         ]

class ReaderPublisher():
    def __init__(self):
        self.modbus_client = ModbusTcpClient(**MODBUS_GW)
        self.read_results = list()
        self.readings_1hr_ago = self.get_historical_data(offset_in_minutes=60)

    def read_and_publish(self):
        self.connect_modbus()
        for m in METERS:
            # store the current for total energy value 
            current_energy_reading = self.total_energy_now(m)
            self.read_results.append(current_energy_reading)

            #calculate and store the consumption for the last hour
            consumed_last_hour = self.total_energy_last_hour(m, current_energy_reading)
            self.read_results.append(consumed_last_hour)

        self.modbus_client.close()
        self._publish_to_mqtt()


    def total_energy_last_hour(self, meter, current_energy_reading):
        meter_id = meter.get('meter_id')
        energy_reading_one_hour_ago = self.readings_1hr_ago.get(meter_id)
        consumed_last_hour = current_energy_reading.get('payload') - energy_reading_one_hour_ago
        pub_topic = meter.get('mqtt_topic_last_hour')
        logger.info(f"{pub_topic} = {consumed_last_hour} kWh")
        return dict(topic=pub_topic, payload = consumed_last_hour)

    @staticmethod
    def get_historical_data(offset_in_minutes):
        logger.info(f"querying influxdb to get historical data for {offset_in_minutes} minutes ago")
        query = f"SELECT * FROM /{INFLUX_TOTAL_ENRGY_MEASUREMENTS}/ \
                  WHERE \
                    time >= now()-{offset_in_minutes-1}m \
                  AND \
                    time < now()={offset_in_minutes-1}m;"

        client = InfluxDBClient(**INLUX_DB)
        result = client.query(query)
        points = result.get_points()
        # points is generator of dicts as {'time': '2021-07-03T16:01:24.519000Z', 'item': 'l2TotalEnergy', 'value': 1250.38} 
        # based on item naming the second char (index=1) is the meter id: 2 in the example above
        results_dict = {int(p.get('item')[1]):p.get('value') for p in points}
        # below condition handles the very first run when no historical data exists in influxdb
        if not results_dict:
            total_energy_items_names=INFLUX_TOTAL_ENRGY_MEASUREMENTS.split('|')
            results_dict = {int(p[1]):0 for p in total_energy_items_names}
        for key, value in results_dict.items():
            logger.info(f"for line '{key}' reading was {value} kWh")
        client.close()
        return results_dict


    def connect_modbus(self, retries = 0):
        connection = self.modbus_client.connect()
        if not connection:
            if (retries < 3):
                time.sleep(1)
                self._connect(self, retries+1) 
            else:
                raise Exception('cannot establish connection to gateway')
        logger.info('connected to Modbus gateway')


    def _read_modbus_registers(self, meter_id):
        result = self.modbus_client.read_holding_registers(address=0,count=2,unit=meter_id)
        if result.isError():   # retry in case of ModbusIOException due to connection issues. 
            logger.warn("invalid result, retrying the read operation...")
            result = self._read_modbus_registers(meter_id)
        return result
    

    def total_energy_now(self, meter):
        meter_id = meter.get('meter_id')
        result = self._read_modbus_registers(meter_id)
        decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big)
        energy_kwh = decoder.decode_32bit_uint() / 100
        pub_topic = meter.get('mqtt_topic_total')
        logger.info(f"{pub_topic} = {energy_kwh} kWh")
        return dict(topic=pub_topic, payload = energy_kwh)


    def _publish_to_mqtt(self):   
        res = publish.multiple(self.read_results, **MQTT_BROKER)

if __name__ == '__main__':
    rp = ReaderPublisher()
    rp.read_and_publish()
