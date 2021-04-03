from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

client = ModbusTcpClient(host='192.168.2.222', port=502)
connection = client.connect()

if connection:
    result = client.read_holding_registers(address=0,count=22,unit=2)
    decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big)
    decoded = {
                "Total kWh": decoder.decode_32bit_uint() / 100,
                "ignore": decoder.skip_bytes(12),
                "Export kWh": decoder.decode_32bit_uint(),
                "Import kWh": decoder.decode_32bit_uint() / 100,
                "Voltage": decoder.decode_16bit_uint() / 10,
                "Current": decoder.decode_16bit_uint() / 100,
                "Active Power": decoder.decode_16bit_uint() / 1000,
                "Reactive Power": decoder.decode_16bit_uint() / 1000,
                "Power factor": decoder.decode_16bit_uint() / 1000,
                "Frequency": decoder.decode_16bit_uint() / 100,
                "ignore": decoder.skip_bytes(6),
                "Meter ID": decoder.decode_8bit_uint(),
                "Baudrate": decoder.decode_8bit_uint() #1, 2, 3 or 4  means  respectively 9600, 4800, 2400 and 1200
                }
    client.close()
    print(decoded)
else:
    print('Connection lost, Try again')