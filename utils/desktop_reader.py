import time
import random

from .serial_com import SerialCom
from .utils import prepareCommand, stringifyHex, splitCommands, filterWithPrefix, encodePrefix, str2tag, startswith

class DesktopReader( object ):

    TAG_LENGTH = 6 # words
    TAG_START = 2 # words
    TAG_LABEL_LENGTH = 3 # words
    STABILIZATION_TIME = 0.3 # seconds

    lock = [ 0x11, 0x22, 0x33, 0x44 ]

    def __init__( self ):
        self.serialCom = SerialCom( portConfigFile='data/desktop_reader_info.txt' )
    
    def readTags( self, prefix=None, seconds=None ):
        seconds = seconds or ( 2 * self.STABILIZATION_TIME )
        inventoryCommand = prepareCommand( [ 0x89, 0x03 ] )
        setWorkingAntennaCommand = prepareCommand( [ 0x74, 0x00 ] )

        self.serialCom.write( inventoryCommand )
        self.serialCom.write( setWorkingAntennaCommand )
        
        allBytes = []
        starttime = time.time()
        while time.time() - starttime < max( self.STABILIZATION_TIME, seconds - self.STABILIZATION_TIME ):
            if self.serialCom.in_waiting:
                data = self.serialCom.read( self.serialCom.in_waiting )
                allBytes += [ x for x in data ]
            time.sleep( 0.01 )
        
        time.sleep( self.STABILIZATION_TIME )
        
        lines = splitCommands( allBytes, 0xA0 )
        tags = set()
        for line in lines:
            if len( line ) < 3 or line[ 2 ] != 0x89: continue
            tag = line[ 2 + self.TAG_START * 2 : 2 + self.TAG_START * 2 + self.TAG_LENGTH * 2 ]
            if len( tag ) != self.TAG_LENGTH * 2: continue
            tags.add( stringifyHex( tag ) )
        tags = [ str2tag( tag ) for tag in tags ]
        return filterWithPrefix( tags, prefix, self.TAG_LABEL_LENGTH * 2 )

    def readTagsWithRetry( self, *args, retries=3, **kwargs ):
        while retries > 0:
            tags = self.readTags( *args, **kwargs )
            if tags:    return tags
            retries -= 1
        return []
    
    def writeTag( self, findPrefix=None, writePrefix=None, seconds=None, password=None, newTag=None, force=False ):
        tags = self.readTagsWithRetry( prefix=findPrefix, seconds=seconds )
        if not tags:
            return "No tags found"
        if len( tags ) > 1:
            return "More than one tag is found"
            
        password = password or [ 0x00, 0x00, 0x00, 0x00 ]

        tag = tags[0]
        
        newTag = []
        if writePrefix:
            encodedPrefix = encodePrefix( writePrefix, self.TAG_LABEL_LENGTH * 2 )
            if startswith( tag, encodedPrefix ) and not force:
                newTag = tag
            else:
                newTag += encodedPrefix
        rem_len = self.TAG_LENGTH * 2 - len( newTag )
        for _ in range( rem_len ):
            newTag.append( random.randint( 0, 255 ) )
        newTag = newTag or newTag

        accessEpcMatch = prepareCommand( [ 0x85, 0x00, self.TAG_LENGTH * 2 ] + tag )
        writeCommand = prepareCommand( [ 0x82 ] + password + [ 0x01, self.TAG_START, self.TAG_LENGTH ] + newTag )
        
        self.serialCom.write( accessEpcMatch )
        time.sleep( self.STABILIZATION_TIME )
        self.serialCom.write( writeCommand )
        time.sleep( self.STABILIZATION_TIME * 2 )

        return ( tag, newTag )
        
    def write( self, bytes ):
        self.serialCom.write( bytes )