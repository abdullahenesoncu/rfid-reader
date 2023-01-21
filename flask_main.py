from flask import Flask, jsonify, request

from utils.desktop_reader import DesktopReader
from utils.utils import stringifyHex

app = Flask(__name__)

@app.route('/writeTag')
def writeTag():
    findPrefix  = request.args.get( 'findPrefix', default=None )
    writePrefix = request.args.get( 'writePrefix', default=None )

    reader = DesktopReader()
    ret = reader.writeTag( findPrefix=findPrefix, writePrefix=writePrefix )
    if isinstance( ret, str ):
        return jsonify(
            {
                'status': False,
                'message': ret,
            }
        )
    endTags = reader.readTagsWithRetry()

    if len( endTags ) != 1 or endTags[0] != ret[ 1 ]:
        return jsonify(
            {
                'status': False,
                'message': 'There is problem on writing tag'
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

if __name__ == '__main__':
    app.run( host="0.0.0.0" )