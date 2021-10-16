# Generic imports
import json # used when storing nrg readings into local json
from datetime import datetime # used to capture time when meter readings are stored
import os # used for file operations

# Establish logging
from libs.logger import logger, LOG_FILE
logger = logger.getChild('nrgreader')

# Pymodbus object
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

# Client to work with influx database
from influxdb import InfluxDBClient

# IP and port of the Modbus TCP gateway
MODBUS_GW = dict(host='192.168.2.222', port=502)

# Energy meters 
METERS = [
            dict(meter_id=10, 
                 influx_measure_base_name='line0'),
            dict(meter_id=11, 
                 influx_measure_base_name='line1'),
            dict(meter_id=2, 
                 influx_measure_base_name='line2'),
            dict(meter_id=3, 
                 influx_measure_base_name='line3'),
            dict(meter_id=4, 
                 influx_measure_base_name='line4'),
            dict(meter_id=5, 
                 influx_measure_base_name='line5')
         ]

# filename of the json where the readings from previous run are stored
READINGS_CACHE = 'readings_cache.json' 

# details of the influx database to store timeseries data into
INLUX_DB = dict(host='192.168.2.8', port=8086, username='ananchev', password='1Race96R', database='openhab')


class Reader():
    def __init__(self, interval="Manual"):
        logger.info(f"Initialising energy reader with interval '{interval}'...")
        self.interval = interval
        self.prev_readings = {}
        self.readings_cache = self.init_readings_cache()
        self.modbus_client = ModbusTcpClient(**MODBUS_GW)
        self.publish_to_influx_lst = []


    def init_readings_cache(self) -> dict:
        readtime = datetime.now()
        readtime_epoch = readtime.timestamp()
        readtime_str = readtime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        # does a local cache dict exist?
        if not os.path.exists(READINGS_CACHE):
            logger.info("Cached results from earlier readings not found. Creating a new file now...")
            new_dict = {self.interval:dict(readtime_epoch=readtime_epoch, 
                                           readtime_str=readtime_str,
                                           readings=list()
                                          )
                                          }
            return new_dict

        with open(READINGS_CACHE, 'r', encoding='utf-8') as f:
            exisiting_dict = json.load(f)

        if self.interval in exisiting_dict: # local cache exists and interval within it exists
            logger.info(f"Cached results from earlier readings found. Copying interval '{self.interval}' from it.")
            self.prev_readings = {key: value for key, value in exisiting_dict.items() if key in self.interval}

            # with open('prev_readings.json', 'w', encoding='utf-8') as f:
            #     json.dump(self.prev_readings, f, ensure_ascii=False, indent=4)

            exisiting_dict.update({self.interval:{'readtime_epoch':readtime_epoch, 'readtime_str':readtime_str, 'readings':list()}})

        else: # local cache existis, but this is the first time we add the current read interval in it 
            logger.info(f"Cached results from earlier readings found, but interval '{self.interval}' does not exist and will be added.")
            exisiting_dict[self.interval] = dict(readtime_epoch=readtime_epoch, 
                                                 readtime_str=readtime_str,
                                                 readings=list()
                                                )
        return exisiting_dict


    def execute(self):
        self.read_current()
        if self.calculate_consumed_energy():
            self.write_to_influx()


    def read_current(self):
        self.connect_modbus()
        for m in METERS:
            # store the current readings for total energy value 
            current_energy_reading = self.total_energy_now(m)
            self.readings_cache[self.interval]['readings'].append(current_energy_reading)

            self.publish_to_influx_lst.append({"measurement":current_energy_reading["measurement_total"], 
                                    "time":self.readings_cache[self.interval]["readtime_str"],
                                    "fields":dict(item=current_energy_reading["measurement_total"],
                                                  value=current_energy_reading["value_total"])})

        self.modbus_client.close()

        with open(READINGS_CACHE, 'w', encoding='utf-8') as f:
            json.dump(self.readings_cache, f, ensure_ascii=False, indent=4)


    def connect_modbus(self, retries = 0):
        connection = self.modbus_client.connect()
        if not connection:
            if (retries < 3):
                time.sleep(1)
                self._connect(self, retries+1) 
            else:
                raise Exception('cannot establish connection to gateway')
        logger.info('connected to Modbus gateway')


    def total_energy_now(self, meter):
        meter_id = meter.get('meter_id')
        result = self.read_modbus_registers(meter_id)
        decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big)
        energy_kwh = decoder.decode_32bit_uint() / 100
        influx_measure = meter.get('influx_measure_base_name')
        logger.info(f"{influx_measure}total = {energy_kwh} kWh")
        return dict(meter_id=meter_id, measurement_total=influx_measure+"Total", value_total = energy_kwh)

    
    def calculate_consumed_energy(self):
        # calculate consumed energy only if previous reading cache for the trigger period is found
        if not self.prev_readings: #empty dict evaluates to false
            logger.info(f"No previous readings exist for trigger interval '{self.interval}'. Consumed energy will be calculated on next trigger.")
            return False

        for m in METERS:
            meter_id = m.get('meter_id')
            meter_prev_reading = next(i for i in self.prev_readings[self.interval]['readings'] if i['meter_id'] == meter_id)
            meter_current_reading = next(j for j in self.readings_cache[self.interval]['readings'] if j['meter_id'] == meter_id)
            #  {"meter_id": 10, "measurement_total": "line0-total", "value_total": 0.95}

            consumed = round(meter_current_reading['value_total'] - meter_prev_reading['value_total'],2)
            logger.info(f"Consumed energy on meter '{meter_id}' for the last '{self.interval}' period is '{consumed}' kWh")

            measure_base_name = m.get('influx_measure_base_name')
            self.publish_to_influx_lst.append({"measurement":measure_base_name+"Last" + self.interval, 
                                               "time":self.readings_cache[self.interval]["readtime_str"],
                                               "fields":dict(item=measure_base_name+"Last" + self.interval,
                                                             value=consumed)})

        # with open("to_pub_to_influx.json", 'w', encoding='utf-8') as f:
        #     json.dump(self.publish_to_influx_lst, f, ensure_ascii=False, indent=4)
        return True

    def write_to_influx(self):
        logger.info("Publishing total and interval results into influx db...")
        client = InfluxDBClient(**INLUX_DB)
        client.write_points(self.publish_to_influx_lst)
        logger.info("Done!")


    def read_modbus_registers(self, meter_id):
        result = self.modbus_client.read_holding_registers(address=0,count=2,unit=meter_id)
        if result.isError():   # retry in case of ModbusIOException due to connection issues. 
            logger.warning("invalid result, retrying the read operation...")
            result = self.read_modbus_registers(meter_id)
        return result