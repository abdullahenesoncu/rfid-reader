import argparse

from utils.desktop_reader import DesktopReader
from utils.utils import stringifyHex

parser = argparse.ArgumentParser( description="Write a tag" )

parser.add_argument( '-p', '--prefix', default=None )

args = parser.parse_args()

reader = DesktopReader()
tags = reader.readTags( prefix=args.prefix )

for tag in tags:
    print( stringifyHex( tag ) )

