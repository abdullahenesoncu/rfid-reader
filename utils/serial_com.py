import serial

class SerialCom( serial.Serial ):
    def __init__( self, *args, portName=None, baudrate=None, portConfigFile=None, **kwargs ):
        assert( ( portName and baudrate ) or portConfigFile )
        if not portName:
            with open( portConfigFile ) as f:
                s = f.readlines()[ 0 ]
                portName = s.split()[ 0 ]
                baudrate = int( s.split()[ 1 ] )
        super( SerialCom, self ).__init__( portName, baudrate, timeout=1 )