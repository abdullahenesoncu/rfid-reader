import argparse

parser = argparse.ArgumentParser( description="Write a tag" )

parser.add_argument( '-b', '--baudrate', type=int, default=None )
parser.add_argument( '-s', '--serial-port', default=None )

args = parser.parse_args()

with open( 'data/desktop_reader_info.txt' ) as f:
    s = f.readlines()[ 0 ]
    portName = args.serial_port or s.split()[ 0 ]
    baudrate = args.baudrate or int( s.split()[ 1 ] )

with open( 'data/desktop_reader_info.txt', 'w' ) as f:
    f.write( f'{portName} {baudrate}' )

args = parser.parse_args()

