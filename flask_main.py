from flask import Flask, jsonify, request

from utils.desktop_reader import DesktopReader
from utils.utils import stringifyHex

app = Flask(__name__)

@app.route('/writeTag')
def writeTag():
    findPrefix  = request.args.get( 'findPrefix', default=None )
    writePrefix = request.args.get( 'writePrefix', default=None )
    passwordStr = request.args.get( 'password', default="00000000" )
    
    password = []
    for i in range( 0, len( passwordStr ), 2 ):
        password.append( int( f'0x{passwordStr[i]}{passwordStr[i+1]}', base=16 ) )

    reader = DesktopReader()
    ret = reader.writeTag( findPrefix=findPrefix, writePrefix=writePrefix, password=password )
    if isinstance( ret, str ):
        return jsonify(
            {
                'status': False,
                'message': ret,
            }
        )
    
    return jsonify(
        {
            'status': True,
            'tag': stringifyHex( ret[ 1 ] ),
        }
    )

@app.route('/readTags')
def readTags():
    prefix  = request.args.get( 'prefix', default=None )

    reader = DesktopReader()
    tags = reader.readTags( prefix=prefix )

    return jsonify(
        {
            'status': True,
            'tags': [ stringifyHex( tag ) for tag in tags ],
        }
    )

@app.route('/readTag')
def readTag():
    prefix = request.args.get( 'prefix', default=None )

    reader = DesktopReader()
    tags = reader.readTags( prefix=prefix )

    if len( tags ) > 1:
        return jsonify(
            {
                'status': False,
                'message': "There is more than one tag",
            }
        )
    elif len( tags ) == 0:
        return jsonify(
            {
                'status': False,
                'message': "There is no tag",
            }
        )
    else:
        return jsonify(
            {
                'status': True,
                'tag': stringifyHex( tags[ 0 ] ),
            }
        )

@app.route('/setPassword')
def setPassword():
    prefix  = request.args.get( 'prefix', default=None )
    oldPasswordStr = request.args.get( 'oldPassword', default="00000000" )
    oldPassword = []
    for i in range( 0, len( oldPasswordStr ), 2 ):
        oldPassword.append( int( f'0x{oldPasswordStr[i]}{oldPasswordStr[i+1]}', base=16 ) )

    reader = DesktopReader()
    tags = reader.readTags( prefix=prefix )
    if len( tags ) > 1:
        return jsonify({
            'status': False,
            'message': 'There is more than one tag with specified prefix'
        })
    
    if len( tags ) == 0:
        return jsonify({
            'status': False,
            'message': 'There is no tag with specified prefix'
        })

    tag = tags[ 0 ]

    reader.unlockTag( tag, oldPassword )
    if not reader.setPassword( tag, oldPassword ) or not reader.lockTag( tag ):
        return jsonify(
            {
                'status': False,
                'message': f'Tag could not locked'
            }
        )
    else:
        return jsonify(
            {
                'status': True,
                'message': f'Password is changed for {stringifyHex(tag)}'
            }
        )

if __name__ == '__main__':
    app.run( host="0.0.0.0" )