#!/bin/bash -eu

# This script runs at boot and starts three other scripts:
# 	- LoadSSD.py to load take any files placed in the CIFS share on the SSD
#	- MergeTeslaCam.py to merge all three camera files into one video
#	- UploadDrive.py to upload selected files to Google Drive
# It also starts filebrowser so the footage can be viewed from a browser.

SCRIPT_PATH=/home/pavan/TeslaCamProcess
LOGFILE=/home/pavan/log/startup.log

function log () {
#  echo "$( date ): $1" >> $LOGFILE
  echo "$( date ): $1"
}

log "Starting up our apps"
/usr/bin/nohup /usr/local/bin/filebrowser -d /home/pavan/filebrowser.db &
/usr/bin/nohup $SCRIPT_PATH/LoadSSD.py &
/usr/bin/nohup $SCRIPT_PATH/MergeTeslaCam.py &
/usr/bin/nohup $SCRIPT_PATH/UploadDrive.py &
log "Started all apps"
