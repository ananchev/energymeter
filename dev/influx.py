from influxdb import InfluxDBClient
from datetime import datetime
import json

INLUX_DB = dict(host='192.168.2.8', port=8086, username='ananchev', password='1Race96R', database='openhab')
INFLUX_TOTAL_ENRGY_MEASUREMENTS = "l0TotalEnergy|l1TotalEnergy|l2TotalEnergy|l3TotalEnergy|l4TotalEnergy|l5TotalEnergy"
 

def query():
    query = f"SELECT * FROM /{INFLUX_TOTAL_ENRGY_MEASUREMENTS}/ \
                WHERE \
                time >= now()-60m \
                AND \
                time < now()-59m;"

    client = InfluxDBClient(**INLUX_DB)
    result = client.query(query)
    pg = result.get_points()
    for p in pg:
        print(p)
    cdict = {p.get('item')[1]:p.get('value') for p in pg}
    # print(cdict)
    if not cdict:
        energy_items=INFLUX_TOTAL_ENRGY_MEASUREMENTS.split('|')
        cdict = {p[1]:0 for p in energy_items}
    # print(cdict)
    client.close()



def write_data():
    data_lst = []
    data_lst.append(dict(measurement="test", time="2009-10-12T23:00:00Z", fields=dict(value=123)))
    data_lst.append(dict(measurement="test", time="2009-12-12T23:00:00Z", fields=dict(value=345)))

    json_str = json.dumps(data_lst)

    client = InfluxDBClient(**INLUX_DB)
    client.write_points(data_lst)

if __name__ == "__main__":
    write_data()