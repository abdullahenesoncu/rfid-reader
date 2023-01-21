import argparse
import sys

from utils.desktop_reader import DesktopReader
from utils.utils import stringifyHex

parser = argparse.ArgumentParser( description="Write a tag" )

parser.add_argument( '-p', '--findPrefix', default=None )
parser.add_argument( '-P', '--writePrefix', default=None )
parser.add_argument( '--password', type=lambda x: int( f'0x{x}', base=16 ), nargs=4, default=None )

args = parser.parse_args()

reader = DesktopReader()
ret = reader.writeTag( findPrefix=args.findPrefix, writePrefix=args.writePrefix, password=args.password)
if isinstance( ret, int ):
    sys.exit( ret )
endTags = reader.readTagsWithRetry()

if len( endTags ) != 1 or endTags[0] != ret[ 1 ]:
    print( "There may be problem, please try again" )

print( stringifyHex( ret[ 1 ] ) )

