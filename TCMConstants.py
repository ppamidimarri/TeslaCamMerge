import logging

# Location where the TeslaCamMerge directory is present. Must NOT include trailing /.
PROJECT_PATH = '/home/pavan'  # Must contain the directory called TeslaCamMerge (where you cloned this repository), as well as filebrowser.db
PROJECT_USER = 'pavan'        # User ID for the application to run as. This user needs to have read permission on all the paths listed here, plus write permission on the SSD and CIFS share

# Locations of the stored footage on the SSD. MUST include trailing /. PROJECT_USER must have read-write permissions on all these paths.
FULL_PATH = '/media/pavan/Samsung_T5/Footage/Full/'           # Where the merged files are stored
RAW_PATH = '/media/pavan/Samsung_T5/Footage/Raw/'             # Where the raw footage from TeslaCam is stored
FAST_PATH = '/media/pavan/Samsung_T5/Footage/Fast/'           # Where the fast preview files are stored
UPLOAD_LOCAL_PATH = '/media/pavan/Samsung_T5/Footage/Upload/' # Any files placed in this directory will be uploaded to Google Drive
SSD_MOUNT_POINT = '/media/pavan/Samsung_T5'                   # Mount point for the SSD

# Location of CIFS share. MUST include trailing /. PROJECT_USER must have read-write permissions.
SHARE_PATH = '/samba/fjnuser/'

# rclone configuration entry for Google Drive.
UPLOAD_REMOTE_PATH = 'gdrive:/TeslaCam' # Properly-configured entry in your rclone.conf file. Any subdirectory must already exist on Google Drive.

# Settings for application logs
LOG_PATH = '/home/pavan/log/' # Must include trailing /, PROJECT_USER needs read-write permissions
LOG_EXTENSION = '.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.DEBUG

# Paths of installed software, including name of the application
FFMPEG_PATH = '/usr/bin/ffmpeg'
RCLONE_PATH = '/usr/local/bin/rclone'
FILEBROWSER_PATH = '/usr/local/bin/filebrowser'
