import logging
import logging.handlers
import os
import subprocess
import re
import sys
import signal

# Location where the TeslaCamMerge directory is present. Must NOT include trailing /.
PROJECT_PATH = '/home/pavan'	# Must contain the directory called TeslaCamMerge (where you cloned this repository), as well as filebrowser.db
PROJECT_USER = 'pavan'		# User ID for the application to run as. This user needs to have read permission on all the paths listed here, plus write permission on the SSD and CIFS share

# Locations of the stored footage on the SSD. MUST include trailing /. PROJECT_USER must have read-write permissions on all these paths.
UPLOAD_LOCAL_PATH = '/home/pavan/Footage/Upload/'	# Any files placed in this directory will be uploaded to Google Drive
SSD_MOUNT_POINT = '/home/pavan'				# Mount point for the SSD

# Folder names for different types of videos
FAST_FOLDER = 'Fast'
FULL_FOLDER = 'Full'
RAW_FOLDER = 'Raw'

# Dimensions of merged video layout
FRONT_WIDTH = 960 # Must be a multiple of 12 (both 3 and 4)
FRONT_HEIGHT = FRONT_WIDTH*3/4
REST_WIDTH = FRONT_WIDTH/3
REST_HEIGHT = FRONT_HEIGHT/3

# TeslaCam input folders. These are the root folders in the
# TeslaCam share (e.g. 'SavedClips', 'SentryClips') in which timestamp
# folders are placed by TeslaCam
FOOTAGE_FOLDERS = ['SavedClips', 'SentryClips']

# Root location of all footage used and created by the application. MUST include trailing /.
FOOTAGE_PATH = '/home/pavan/Footage/'

# This app can handle footage from multiple cars with Tesla dashcam features.
# If you have more than one Tesla, set MULTI_CAR to True and set up the names
# of the folders for the footage in CAR_LIST. For example, you may want paths
# like '/home/user/Footage/Car1/' and '/home/user/Footage/Car2/' as the paths
# for the footage from each car. Then CAR_LIST should be ['Car1', 'Car2'].
# The order of cars here should match the order of SHARE_PATHS below.
MULTI_CAR = True
CAR_LIST = ['MSM', 'PW']

# Locations of CIFS shares. All paths MUST include trailing /. PROJECT_USER
# must have read-write permissions to all paths. List MUST contain at least one
# path. If you have more than one Tesla, set up one CIFS share location for
# each car, and add all of them to this list. The order of paths here should
# match the order of CAR_LIST above.
SHARE_PATHS = ['/samba/fjnuser/', '/samba/fjnuser2/']

# rclone configuration entry for Google Drive. UPLOAD_REMOTE_PATH
# should be a properly-configured entry in your rclone.conf file.
# Any subdirectory must already exist on Google Drive.
UPLOAD_REMOTE_PATH = 'gdrive:/TeslaCam'

# Number of days to keep videos: applies to raw, full and fast videos.
# Videos that are older than these and in the FULL_PATH, FAST_PATH and
# RAW_PATH locations are automatically deleted by removeOld.service
# To keep videos longer, move them to any other directory, or move to
# the UPLOAD_PATH so they are automatically backed up to cloud storage.
DAYS_TO_KEEP = 30

# Filename for an html file with statistics about TeslaCamMerge.
# If STATS_FILENAME is not empty, the application will generate a
# file in the footage directory (i.e. one level up from RAW_PATH)
# that shows how many videos are in which folder, and the overall
# disk usage. It then converts the HTML into an image using
# cutycapt. If the image is successfully created, it then deletes
# the HTML file. Stats are generated when current timestamp's minute
# matches one of the values in STATS_FREQUENCY, so if you want
# stats updated more frequently, add more numbers between 0 and
# 59 to the list.
STATS_FILENAME = 'stats.html'
STATS_IMAGE = 'stats.png'
STATS_FREQUENCY = [0, 30]
STATS_TIMESTAMP_FORMAT = '%-I:%M %p on %a %b %-d, %Y'

# Settings for application logs
LOG_PATH = '/home/pavan/log/'	# Must include trailing /, PROJECT_USER needs read-write permissions
LOG_EXTENSION = '.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO

# Logging settings for TimedRotatingFileHandler, refer to:
# https://docs.python.org/3.6/library/logging.handlers.html#timedrotatingfilehandler
# for details about the three supported options. The default
# is to rotate once a day and keep ten days' worth of logs.
LOG_WHEN = 'd'
LOG_INTERVAL = 1
LOG_BACKUP_COUNT = 10

# Paths of installed software, including name of the application
FFMPEG_PATH = '/usr/bin/ffmpeg'							# Verify with: which ffmpeg
RCLONE_PATH = '/usr/local/bin/rclone --log-file /home/pavan/log/rclone.log'	# Verify with: which rclone
FILEBROWSER_PATH = '/usr/local/bin/filebrowser'					# Verify with: which filebrowser
LSOF_PATH = '/usr/bin/lsof -t'							# Verify with: which lsof
DF_PATH = '/bin/df'								# Verify with: which df
CUTYCAPT_PATH = '/usr/bin/cutycapt --zoom-factor=1.5'				# Verify with: which cutycapt
SYSTEMCTL_PATH = "/bin/systemctl"						# Verify with: which systemctl
XVFB_RUN_PATH = '/usr/bin/xvfb-run'						# Verify with: which xvfb-run

# Video watermark timestamp format (see Python strftime reference)
WATERMARK_TIMESTAMP_FORMAT = '%b %-d\, %-I\:%M %p'		# For file timestamp, without seconds
EVENT_TIMESTAMP_FORMAT = '%b %-d\, %-I\:%M\:%S %p'		# For event timestamp with seconds

# Names of text files to be placed in RAW_PATH that will list bad input files
# created by TeslaCam. BAD_VIDEOS_FILENAME will contain the names of files that
# FFMPEG reports errors for (e.g. moov atom not found). BAD_SIZES_FILENAME
# will contain one row for each timestamps where the sizes of the three files
# drastically different (i.e. outside the range specified below in SIZE_RANGE)
BAD_VIDEOS_FILENAME = 'bad_videos.txt'
BAD_SIZES_FILENAME = 'bad_sizes.txt'

### Do not modify anything below this line ###

# Characteristics of filenames output by TeslaCam
FRONT_TEXT = 'front.mp4'
LEFT_TEXT = 'left_repeater.mp4'
RIGHT_TEXT = 'right_repeater.mp4'
BACK_TEXT = 'back.mp4'
FULL_TEXT = 'full.mp4'
FAST_TEXT = 'fast.mp4'
FILENAME_TIMESTAMP_FORMAT = '%Y-%m-%d_%H-%M-%S'
FILENAME_REGEX  = '(\d{4}(-\d\d){2}_(\d\d-){3})(right_repeater|front|left_repeater|back).mp4'
FILENAME_PATTERN = re.compile(FILENAME_REGEX)
EVENT_JSON = 'event.json'

### Characteristics of event.json files output by TeslaCam
EVENT_DURATION = 600		# Maximum duration in seconds between the timestamp in event.json and the timestamp in the filename
EVENT_REASON = {'sentry_aware_object_detection' : 'Sentry triggered',
	'user_interaction_honk' : 'Honked',
	'user_interaction_dashcam_panel_save' : 'Saved',
	'user_interaction_dashcam_icon_tapped' : 'Saved from viewer'}
EVENT_CAMERA = {'0' : 'front camera',
	'3' : 'left camera',
	'4' : 'right camera'}

# Application management constants
SLEEP_DURATION = 60		# Seconds between looping in main tasks
SPECIAL_EXIT_CODE = 115		# Exit code used by the app, has to be non-zero for systemctl to auto-restart crashed services
SIZE_RANGE = 0.99		# Maximum size difference in percentage between video files, timsestamps with bigger size differences are not merged
FFMPEG_TIMELIMIT = 9000		# CPU time limit in seconds for FFMPEG commands to run

# Common functions

def check_permissions(path, test_write):
	logger = logging.getLogger(get_basename())
	if os.access(path, os.F_OK):
		logger.debug("Path {0} exists".format(path))
		if os.access(path, os.R_OK):
			logger.debug("Can read at path {0}".format(path))
			if test_write:
				if os.access(path, os.W_OK):
					logger.debug("Can write to path {0}".format(path))
					return True
				else:
					logger.error("Cannot write to path {0}".format(path))
					return False
			else:
				return True
		else:
			logger.error("Cannot read at path {0}".format(path))
			return False
	else:
		logger.error("Path {0} does not exist".format(path))
		return False

def check_file_for_read(file):
	if os.access(file, os.F_OK):
		return not file_being_written(file)
	else:
		logging.getLogger(get_basename()).debug(
			"File {0} does not exist".format(file))
		return False

def file_being_written(file):
	logger = logging.getLogger(get_basename())
	completed = subprocess.run("{0} {1}".format(LSOF_PATH, file), shell=True,
		stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	if completed.stderr:
		logger.error("Error running lsof on file {0}, stdout: {1}, stderr: {2}".format(
			file, completed.stdout, completed.stderr))
		return True # abundance of caution: if lsof won't run properly, say file is not ready for read
	else:
		if completed.stdout:
			logger.debug("File {0} in use, stdout: {1}, stderr: {2}".format(
				file, completed.stdout, completed.stderr))
			return True
		else:
			return False

def check_file_for_write(file):
	if os.access(file, os.F_OK):
		logging.getLogger(get_basename()).debug("File {0} exists".format(file))
		return False
	else:
		return True

def exit_gracefully(signum, frame):
	logging.getLogger(get_basename()).info("Received signal {0}, exiting".format(signum))
	exit(signum)

def get_logger():
	basename = get_basename()
	logger = logging.getLogger(basename)
	logger.setLevel(LOG_LEVEL)
	fh = logging.handlers.TimedRotatingFileHandler(
		LOG_PATH + basename + LOG_EXTENSION,
		when=LOG_WHEN, interval=LOG_INTERVAL,
		backupCount=LOG_BACKUP_COUNT)
	fh.setLevel(LOG_LEVEL)
	formatter = logging.Formatter(LOG_FORMAT)
	fh.setFormatter(formatter)
	logger.addHandler(fh)
	logger.info("Starting up")
	signal.signal(signal.SIGINT, exit_gracefully)
	signal.signal(signal.SIGTERM, exit_gracefully)
	return logger

def get_basename():
	return os.path.splitext(os.path.basename(sys.argv[0]))[0]

def convert_file_size(size):
	if size <= 1024:
		return "{0:-6d}B".format(size)
	elif size <= 1024*1024:
		return "{0:-6.1f}K".format(size/1024)
	elif size <= 1024*1024*1024:
		return "{0:-6.1f}M".format(size/(1024*1024))
	elif size <= 1024*1024*1024*1024:
		return "{0:-6.1f}G".format(size/(1024*1024*1024))
	else:
		return "{0:-6.1f}T".format(size/(1024*1024*1024*1024))
