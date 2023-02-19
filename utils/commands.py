import time

from utils.utils import getCheckSum, Hex, splitCommands, stringifyHex, tabulateObjects
import json

ERROR_CODES = json.load( open( 'data/error_codes.json', 'r' ) )
ID2COMMANDS = {
    0X74: "SET_WORK_ANTENNA",
    0x76: "SET_RF_OUTPUT_POWER",
    0X80: "INVENTORY",
    0X81: "READ",
    0X82: "WRITE",
    0X83: "LOCK",
    0X85: "SET_ACCESS_EPC_MATCH",
    0X89: "REAL_TIME_INVENTORY",
}

class Result( object ):
    def __init__( self, **kwargs ):
        self.status = False
        self.errorCode = 0x10
        self.__dict__.update( kwargs )
        self.errorMessage = ERROR_CODES[ Hex( self.errorCode ) ]

class Command( object ):
    HEAD = 0xA0
    ADDRESS = 0x01
    COMMAND_CODE = None
    MULTILINE_OUTPUT = False
    STABILIZATION_TIME = 0.6

    def __init__( self, serialCom, **kwargs ):
        self.serialCom = serialCom
        self.__dict__.update( kwargs )
        self.validate()
    
    def validate( self ):
        return True

    def prepare( self, cmd=[] ):
        cmd = [ self.COMMAND_CODE ] + cmd
        cmd = [ self.ADDRESS ] + cmd
        cmd = [ len( cmd ) + 1 ] + cmd
        cmd = [ self.HEAD ] + cmd
        cmd += [ getCheckSum( cmd ) ]
        return cmd
    
    def endWithPacket( self, packet ):
        return False
    
    def getOutputs( self ):
        results = []
        starttime = time.time()
        outputted = False
        while time.time() - starttime < self.STABILIZATION_TIME or not outputted:
            if self.serialCom.in_waiting:
                outputted = True
                data = self.serialCom.read( self.serialCom.in_waiting )
                packets = splitCommands( [ x for x in data ], self.HEAD )
                failed = False
                end = False
                for packet in packets:
                    end = end or self.endWithPacket( packet )
                    interprettedPacket = self.interpretPacket( packet )
                    if not interprettedPacket:
                        continue
                    results.append( interprettedPacket )
                    if not interprettedPacket.status:
                        failed = True
                if not self.MULTILINE_OUTPUT or failed or end:
                    break
            time.sleep( 0.01 )
        
        return results

    def run( self, verbose=True ):
        self.validate()
        command = self.prepare([])
        print( "\n\n================================================================" )
        print( stringifyHex(command) )
        print( ID2COMMANDS[ self.COMMAND_CODE ] )
        tabulateObjects( [ self ] )
        self.serialCom.write( command )
        results = self.getOutputs()
        print( "\n" )
        tabulateObjects( results )
        return results

class WriteCommand( Command ):
    COMMAND_CODE = 0x82
    MULTILINE_OUTPUT = True

    def __init__( self, serialCom, password, menBank, wordAdd, wordCnt, data ):
        super().__init__( 
            serialCom,
            password=password, menBank=menBank, wordAdd=wordAdd, wordCnt=wordCnt, data=data
        )
    
    def validate( self ):
        assert len( self.data ) == self.wordCnt * 2
        assert 0x00 <= self.menBank < 0x04
        if self.menBank == 0x00:
            assert self.wordAdd == 0x02 and self.wordCnt == 0x02
        elif self.menBank == 0x01:
            assert self.wordAdd == 0x02
        else:
            raise NotImplementedError()
    
    def prepare( self, cmd=[] ):
        cmd += self.password
        cmd += [ self.menBank, self.wordAdd, self.wordCnt ]
        cmd += self.data
        cmd = super().prepare( cmd )
        return cmd
    
    def interpretPacket( self, packet ):
        if packet[ 1 ] == 0x04:
            return Result( status=False, errorCode=packet[ 4 ] )
        else:
            result = Result(
                status=True,
                errorCode=packet[ -4 ],
                dataLen=packet[ 6 ],
                data=packet[ 7 : 7 + packet[ 6 ] ]
            )
            if self.menBank == 0x00 or self.menBank == 0x01:
                result.data = result.data[ 2 : ]
            return result

class ReadCommand( Command ):
    COMMAND_CODE = 0x81
    MULTILINE_OUTPUT = True

    def __init__( self, serialCom, menBank, wordAdd, wordCnt ):
        super().__init__(
            serialCom,
            menBank=menBank, wordAdd=wordAdd, wordCnt=wordCnt
        )
    
    def validate( self ):
        assert 0x00 <= self.menBank < 0x04
        if self.menBank == 0x00:
            assert self.wordAdd == 0x02 and self.wordCnt == 0x02
        elif self.menBank == 0x01:
            assert self.wordAdd == 0x02
        else:
            raise NotImplementedError()
    
    def prepare( self, cmd=[] ):
        cmd += [ self.menBank, self.wordAdd, self.wordCnt ]
        cmd = super().prepare( cmd )
        return cmd
    
    def interpretPacket( self, packet ):
        if packet[ 1 ] == 0x04:
            return Result( status=False, errorCode=packet[ 4 ] )
        else:
            result = Result(
                status=True,
                errorCode=packet[ -4 ],
                dataLen=packet[ 6 ],
                data=packet[ 7 : 7 + packet[ 6 ] ]
            )
            if self.menBank == 0x00 or self.menBank == 0x01:
                result.data = result.data[ 2 : ]
            return result

class RealTimeInventoryCommand( Command ):
    COMMAND_CODE = 0x89
    MULTILINE_OUTPUT = True

    def __init__( self, serialCom, repeat ):
        super().__init__( 
            serialCom,
            repeat=repeat,
        )
    
    def validate( self ):
        assert 0 < self.repeat < 256
    
    def prepare( self, cmd=[] ):
        cmd += [ self.repeat ]
        cmd = super().prepare( cmd )
        return cmd
    
    def interpretPacket( self, packet ):
        if packet[ 1 ] == 0x04 or packet[ 1 ] == 0x0A:
            return None
        else:
            return Result(
                status=True,
                epcData=packet[ 7 : -2 ]
            )
    
    def endWithPacket( self, packet ):
        return packet[ 1 ] == 0x04 or packet[ 1 ] == 0x0A

class SetWorkAntennaCommand( Command ):
    COMMAND_CODE = 0x74
    MULTILINE_OUTPUT = False

    def __init__( self, serialCom, antennaId ):
        super().__init__( 
            serialCom,
            antennaId=antennaId,
        )
    
    def prepare( self, cmd=[] ):
        cmd += [ self.antennaId ]
        cmd = super().prepare( cmd )
        return cmd
    
    def interpretPacket( self, packet ):
        return Result(
            status=( packet[ 4 ] == 0x10 ),
            errorCode=packet[ 4 ],
        )

class SetAccessEpcMatchCommand( Command ):
    COMMAND_CODE = 0x85
    MULTILINE_OUTPUT = False

    def __init__( self, serialCom, mode, epc ):
        epcLen = len( epc )
        super().__init__( 
            serialCom,
            mode=mode, epcLen=epcLen, epc=epc,
        )
    
    def validate( self ):
        assert self.epcLen == len( self.epc )
    
    def prepare( self, cmd=[] ):
        cmd += [ self.mode, self.epcLen ] + self.epc
        cmd = super().prepare( cmd )
        return cmd
    
    def interpretPacket( self, packet ):
        return Result(
            status=( packet[ 4 ] == 0x10 ),
            errorCode=packet[ 4 ],
        )

class LockCommand( Command ):
    COMMAND_CODE = 0x83
    MULTILINE_OUTPUT = True

    def __init__( self, serialCom, password, menBank, lockType ):
        super().__init__( 
            serialCom,
            password=password, menBank=menBank, lockType=lockType,
        )
    
    def validate( self ):
        assert 0x00 < self.menBank < 0x06
        if self.menBank != 0x03 and self.menBank != 0x04:
            raise NotImplementedError()
        if self.lockType != 0x00 and self.lockType != 0x01:
            raise NotImplementedError()
    
    def prepare( self, cmd=[] ):
        cmd += self.password
        cmd += [ self.menBank, self.lockType ]
        cmd = super().prepare( cmd )
        return cmd
    
    def interpretPacket( self, packet ):
        if packet[ 1 ] == 0x04:
            return Result( status=False, errorCode=packet[ 4 ] )
        else:
            result = Result(
                status=True,
                errorCode=packet[ -4 ],
                dataLen=packet[ 6 ],
                data=packet[ 7 : 7 + packet[ 6 ] ]
            )
            if self.menBank == 0x00 or self.menBank == 0x01:
                result.data = result.data[ 2 : ]
            return result

class SetRFOutputPowerCommand( Command ):
    COMMAND_CODE = 0x76
    MULTILINE_OUTPUT = False

    def __init__( self, serialCom, power ):
        super().__init__( 
            serialCom,
            power=power,
        )
    
    def validate( self ):
        assert 0x12<=self.power<=0x1A
    
    def prepare( self, cmd=[] ):
        cmd += [ self.power ]
        cmd = super().prepare( cmd )
        return cmd
    
    def interpretPacket( self, packet ):
        return Result(
            status=( packet[ 4 ] == 0x10 ),
            errorCode=packet[ 4 ],
        )