from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

def validator(instance):
    if not instance.isError():
        '''.isError() implemented in pymodbus 1.4.0 and above.'''
        decoder = BinaryPayloadDecoder.fromRegisters(
            instance.registers,
            byteorder=Endian.Big, wordorder=Endian.Little
        )   
        return float('{0:.2f}'.format(decoder.decode_32bit_float()))

    else:
        # Error handling.
        print("There isn't the registers, Try again.")
        return None

client = ModbusTcpClient(host='192.168.2.222', port=502)
connection = client.connect()

if connection:
    result = client.read_holding_registers(address=0,count=22,unit=2)
    print(result.registers)
    client.close()
else:
    print('Connection lost, Try again')