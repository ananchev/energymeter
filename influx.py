from influxdb import InfluxDBClient

INLUX_DB = dict(host='192.168.2.8', port=8086, username='ananchev', password='1Race96R', database='openhab')
INFLUX_TOTAL_ENRGY_MEASUREMENTS = "l2TotalEnergy|l5TotalEnergy"

query = f"SELECT * FROM /{INFLUX_TOTAL_ENRGY_MEASUREMENTS}/ WHERE time >= now()-60m;"

client = InfluxDBClient(**INLUX_DB)
result = client.query(query)
pg = result.get_points()
cdict = {p.get('item')[1]:p.get('value') for p in pg}
print(cdict)
if not cdict:
    energy_items=INFLUX_TOTAL_ENRGY_MEASUREMENTS.split('|')
    cdict = {p[1]:0 for p in energy_items}
print(cdict)
client.close()