import time
import random

from datetime import datetime

from .commands import *
from .serial_com import SerialCom
from .utils import stringifyHex, filterWithPrefix, encodePrefix, str2tag, startswith

class DesktopReader( object ):

    TAG_LENGTH = 6 # words
    TAG_START = 2 # words
    TAG_LABEL_LENGTH = 3 # words

    password = [ 0x17, 0x03, 0x77, 0xF5 ]

    def __init__( self ):
        self.serialCom = SerialCom( portConfigFile='data/desktop_reader_info.txt' )

    def setAccessEpcMatch( self, tag ):
        return SetAccessEpcMatchCommand( self.serialCom, 0x00, tag ).run()[ 0 ].status

    def setPassword( self, tag, oldPassword=None, newPassword=None ):
        oldPassword = oldPassword or [ 0x00, 0x00, 0x00, 0x00 ]
        newPassword = newPassword or self.password
        
        if not self.setAccessEpcMatch( tag ):
            return False

        return WriteCommand( self.serialCom, oldPassword, 0x00, 0x02, 0x02, newPassword ).run()[ 0 ].status

    def lockHelper( self, password, menBank, mode ):
        return LockCommand( self.serialCom, password, menBank, mode ).run()[ 0 ].status

    def lockTag( self, tag, password=None ):
        password = password or self.password

        if not self.setAccessEpcMatch( tag ):
            return False
        
        if not self.doWithRetry( lambda: self.lockHelper( password, 0x03, 0x01 ) ):
            return False

        if not self.doWithRetry( lambda: self.lockHelper( password, 0x04, 0x01 ) ):
            return False
        
        return True
    
    def unlockTag( self, tag, password=None ):
        password = password or [ 0x00, 0x00, 0x00, 0x00 ]

        if not self.setAccessEpcMatch( tag ):
            return False
        
        if not self.doWithRetry( lambda: self.lockHelper( password, 0x03, 0x00 ) ):
            return False

        if not self.doWithRetry( lambda: self.lockHelper( password, 0x04, 0x00 ) ):
            return False
        
        return True
    
    def readTags( self, prefix=None ):
        SetWorkAntennaCommand( self.serialCom, 0x00 ).run()
        results = RealTimeInventoryCommand( self.serialCom, 0x03 ).run()
        
        tags = set()
        for result in results:
            tags.add( stringifyHex( result.epcData ) )
        tags = [ str2tag( tag ) for tag in tags ]

        return filterWithPrefix( tags, prefix, self.TAG_LABEL_LENGTH * 2 )

    def setPower( self, power ):
        SetRFOutputPowerCommand( self.serialCom, power ).run()
    
    def doWithRetry( self, func, *args, retries=3, **kwargs ):
        while retries > 0:
            res = func( *args, **kwargs )
            if res:    return res
            retries -= 1
        return None  
    
    def writeTag( self, findPrefix=None, writePrefix=None, password=None, newTag=None, force=True ):
        tags = self.doWithRetry( self.readTags, prefix=findPrefix )
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

        if not self.doWithRetry( self.unlockTag, tag, password ):
            return 'Error, problem on unlocking tag'

        if not self.setAccessEpcMatch( tag ):
            return 'Problem on setting access epc match'

        if not WriteCommand( self.serialCom, password, 0x01, self.TAG_START, self.TAG_LENGTH, newTag ).run()[ 0 ].status:
            return "There is some problem on writing the tag"

        if not self.setPassword( newTag, oldPassword=password ):
            return "Error, problem on set password"

        if not self.lockTag( newTag ):
            return "Error, problem on lock tag"

        return ( tag, newTag )