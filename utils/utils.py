import hashlib
from tabulate import tabulate

def getCheckSum( arr ):
    sum = 0
    for x in arr: sum += x
    return ( ~( sum % 256 ) + 1 ) % 256

def prepareCommand( arr, deviceId=1 ):
    arr = [ deviceId ] + arr
    arr = [ 0xA0 ] + [ len( arr ) + 1 ] + arr
    arr += [ getCheckSum( arr ) ]
    return bytearray( arr )

def hex( x ):
    return '{0:0{1}X}'.format( x, 2 )

def Hex( x ):
    return '0x{0:0{1}X}'.format( x, 2 )

def stringifyHex( arr ):
    return ' '.join( [ hex( x ) for x in arr ] )

def str2tag( s ):
    return [ int( f'0x{hex}', base=16 ) for hex in s.split() ]

def splitCommands( lst, seperator ):
    res = []
    i = 0
    while i < len( lst ):
        try:
            if lst[ i ] == seperator:
                length = lst[ i + 1 ]
                command = lst[ i : i + length + 2 ]
                if len( command ) == length + 2:
                    res.append( command )
                i = i + length + 2
            else:
                i += 1
        except:
            i += 1
    return res

def encodePrefix( prefix, encodedLength ):
    digest = hashlib.md5( prefix.encode( 'utf-8' ) ).digest()
    code = []
    for i in range( encodedLength ):
        code.append( digest[ i % len( digest ) ] )
    return code

def startswith( lst, prefix ):
    if len( prefix ) > len( lst ):  return False
    for x, y in zip( lst[ : len( prefix ) ], prefix ):
        if x != y: return False
    return True

def filterWithPrefix( tags, prefix, encodedLength ):
    if prefix is None: return tags
    code = encodePrefix( prefix, encodedLength )
    res = []
    for tag in tags:
        if startswith( tag, code ):
            res.append( tag )
    return res

def isPrimitive(obj):
    return not hasattr(obj, '__dict__')

def tabulateObjects( objList ):
    keys = set()
    for obj in objList:
        for key, value in obj.__dict__.items():
            if key.upper() == key:
                continue
            if not isPrimitive( value ):
                continue
            keys.add( key )
    
    keys = sorted( list( keys ) )
    values = []
    for obj in objList:
        value = []
        for key in keys:
            v = getattr( obj, key, '' )
            if isinstance( v, int ) and not isinstance( v, bool ):
                v = hex( v )
            if isinstance( v, list ) and isinstance( v[0], int ):
                v = stringifyHex( v )
            value.append( v )
        values.append( value )
    
    print( tabulate( values, headers=keys ) )