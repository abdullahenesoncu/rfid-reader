import hashlib

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
                command = lst[ i + 1 : i + 1 + length ]
                if len( command ) == length:
                    res.append( command )
                i = i + 1 + length
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