import logging

# Location where the TeslaCamMerge directory is present. Must NOT include trailing /
PROJECT_PATH = '/home/pavan'

# Locations of the stored footage on the SSD. MUST include trailing /
FULL_PATH = '/media/pavan/Samsung_T5/Footage/Full/'
RAW_PATH = '/media/pavan/Samsung_T5/Footage/Raw/'
FAST_PATH = '/media/pavan/Samsung_T5/Footage/Fast/'
UPLOAD_LOCAL_PATH = '/media/pavan/Samsung_T5/Footage/Upload/'

# Location of CIFS share. MUST include trailing /
SHARE_PATH = '/samba/fjnuser/'

# Location of rclone entry for Google Drive
UPLOAD_REMOTE_PATH = 'gdrive:/TeslaCam'

# Settings for application logs
LOG_PATH = '/home/pavan/log/' # Must include trailing /
LOG_EXTENSION = '.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.DEBUG

# Paths of installed software, including name of the application
FFMPEG_PATH = '/usr/bin/ffmpeg'
RCLONE_PATH = '/usr/local/bin/rclone'
FILEBROWSER_PATH = '/usr/local/bin/filebrowser'
