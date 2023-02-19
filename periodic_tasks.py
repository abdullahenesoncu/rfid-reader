import os

from apscheduler.schedulers.background import BackgroundScheduler

from utils.desktop_reader import DesktopReader
from utils.json_manager import JsonManager
from utils.state_manager import stateManager
from utils.utils import stringifyHex

def handleCountings():
    for deviceName, data in stateManager:
        if data[ 'status' ] != 'counting':
            continue
        countingName = data[ 'countingName' ]
        jsonManager = JsonManager( os.path.join( 'countings', countingName + '.json' ) )
        reader = DesktopReader()
        reader.setPower( 0x1A )
        tags = reader.readTags()
        reader.setPower( 0x12 )
        for tag in tags:
            jsonManager[ stringifyHex( tag ) ] = { 'status': True }

scheduler = BackgroundScheduler()
scheduler.add_job(func=handleCountings, trigger='interval', seconds=1)
scheduler.start()