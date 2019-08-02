import logging
import os
import subprocess

# Location where the TeslaCamMerge directory is present. Must NOT include trailing /.
PROJECT_PATH = '/home/pavan'	# Must contain the directory called TeslaCamMerge (where you cloned this repository), as well as filebrowser.db
PROJECT_USER = 'pavan'		# User ID for the application to run as. This user needs to have read permission on all the paths listed here, plus write permission on the SSD and CIFS share

# Locations of the stored footage on the SSD. MUST include trailing /. PROJECT_USER must have read-write permissions on all these paths.
FULL_PATH = '/media/pavan/Samsung_T5/Footage/Full/'		# Where the merged files are stored
RAW_PATH = '/media/pavan/Samsung_T5/Footage/Raw/'		# Where the raw footage from TeslaCam is stored
FAST_PATH = '/media/pavan/Samsung_T5/Footage/Fast/'		# Where the fast preview files are stored
UPLOAD_LOCAL_PATH = '/media/pavan/Samsung_T5/Footage/Upload/'	# Any files placed in this directory will be uploaded to Google Drive
SSD_MOUNT_POINT = '/media/pavan/Samsung_T5'			# Mount point for the SSD

# Location of CIFS share. MUST include trailing /. PROJECT_USER must have read-write permissions.
SHARE_PATH = '/samba/fjnuser/'

# rclone configuration entry for Google Drive.
UPLOAD_REMOTE_PATH = 'gdrive:/TeslaCam'	# Properly-configured entry in your rclone.conf file. Any subdirectory must already exist on Google Drive.

# Settings for application logs
LOG_PATH = '/home/pavan/log/'	# Must include trailing /, PROJECT_USER needs read-write permissions
LOG_EXTENSION = '.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO

# Paths of installed software, including name of the application
FFMPEG_PATH = '/usr/bin/ffmpeg'							# Verify with: which ffmpeg
RCLONE_PATH = '/usr/local/bin/rclone --log-file /home/pavan/log/rclone.log'	# Verify with: which rclone
FILEBROWSER_PATH = '/usr/local/bin/filebrowser'					# Verify with: which filebrowser
LSOF_PATH = '/usr/bin/lsof -t'							# Verify with: which lsof

### Do not modify anything below this line ###

SLEEP_DURATION = 60
SPECIAL_EXIT_CODE = 115

def check_permissions(path, test_write, logger):
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

def check_file_for_read(file, logger):
	if os.access(file, os.F_OK):
		return not file_being_written(file, logger)
	else:
		logger.warn("File {0} does not exist".format(file))
		return False

def file_being_written(file, logger):
	completed = subprocess.run("{0} {1}".format(LSOF_PATH, file), shell=True,
		stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	if completed.stderr:
		logger.error("Error running lsof on file {0}, stdout: {1}, stderr: {2}".format(
			file, completed.stdout, completed.stderr))
		return True # abundance of caution: if lsof won't run properly, postpone the merge!
	else:
		if completed.stdout:
			logger.info("File {0} in use, stdout: {1}, stderr: {2}".format(
				file, completed.stdout, completed.stderr))
			return True
		else:
			return False

def check_file_for_write(file, logger):
	if os.access(file, os.F_OK):
		logger.debug("File {0} exists".format(file))
		return False
	else:
		return True
