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
        tags = reader.readTags()
        for tag in tags:
            jsonManager[ stringifyHex( tag ) ] = { 'status': True }

scheduler = BackgroundScheduler()
scheduler.add_job(func=handleCountings, trigger='interval', seconds=0.3)
scheduler.start()