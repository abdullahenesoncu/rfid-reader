import functools
import json
import os
import threading

from flask import Flask, jsonify, request

from utils.desktop_reader import DesktopReader
from utils.state_manager import stateManager
from utils.utils import stringifyHex

app = Flask(__name__)
locks = {}

import periodic_tasks as _

def lock_request(acquire_lock=True, release_lock=True, deviceName='desktopReader'):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if deviceName not in locks:
                locks[ deviceName ] = threading.Lock()
            lock = locks[ deviceName ]

            if not acquire_lock:
                lock_acquired = True
            else:
                lock_acquired = lock.acquire(blocking=False)

            if not lock_acquired:
                return '404', 404
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                # Handle the exception if needed
                print(f"Error occurred: {e}")
                raise e
            finally:
                if release_lock and lock.locked():
                    lock.release()

            return result
        wrapper.__name__ = f"{func.__name__}_wrapper"
        return wrapper
    return decorator

@app.route('/writeTag')
@lock_request()
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
@lock_request()
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
@lock_request()
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
@lock_request()
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

@app.route('/startCounting')
@lock_request(release_lock=False)
def startCounting():
    countingName = request.args.get( 'countingName' )
    deviceName = request.args.get( 'deviceName', default='desktopReader' )
    if stateManager[ f'{deviceName}.status' ] != "open":
        return jsonify(
            {
                'status': False,
                'message': f'Device {deviceName} is busy',
            }
        )
    stateManager[ f'{deviceName}.status' ] = "counting"
    stateManager[ f'{deviceName}.countingName' ] = countingName
    return jsonify(
        {
            'status': True,
            'countingName': countingName,
        }
    )

@app.route('/endCounting')
@lock_request(acquire_lock=False)
def endCounting():
    countingName = request.args.get( 'countingName' )
    deviceName = request.args.get( 'deviceName', default='desktopReader' )
    if stateManager[ f'{deviceName}.status' ] != "counting" or stateManager[ f'{deviceName}.countingName' ] != countingName:
        return jsonify(
            {
                'status': False,
                'message': f'Invalid end operation',
            }
        )
    stateManager[ f'{deviceName}.status' ] = "open"
    del stateManager[ f'{deviceName}.countingName' ]
    data = {}
    try:
        with open( os.path.join( 'countings', countingName + '.json' ) ) as f:
            data = json.load( f )
    except:
        pass
    return jsonify(
        {
            'status': True,
            'countingName': countingName,
            'data': data,
        }
    )

@app.route('/getCountingData')
def getCountingData():
    countingName = request.args.get( 'countingName' )
    data = {}
    try:
        with open( os.path.join( 'countings', countingName + '.json' ) ) as f:
            data = json.load( f )
    except:
        pass
    return jsonify(
        {
            'status': True,
            'countingName': countingName,
            'data': data,
        }
    )

if __name__ == '__main__':
    app.run( host="0.0.0.0" )