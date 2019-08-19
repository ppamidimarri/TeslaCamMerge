#!/usr/bin/env python3

# This script removes:
# 	- empty directories within "SOURCE_PATH"
#	- video files under "VIDEO_PATHS"
# that have a name with a timestamp more than "DAYS_TO_KEEP" days old
# Files and directories who names don't match this format are left alone

import os
import time
import shutil
import signal
import logging
import logging.handlers
import TCMConstants
import Stats
import datetime
import re

SOURCE_PATH = TCMConstants.SHARE_PATH
VIDEO_PATHS = [TCMConstants.RAW_PATH, TCMConstants.FULL_PATH, TCMConstants.FAST_PATH]
ALL_VIDEO_REGEX = "{0}|fast|full).mp4".format(TCMConstants.FILENAME_REGEX[:-5])
ALL_VIDEO_PATTERN = re.compile(ALL_VIDEO_REGEX)

logger_name = 'RemoveOld'
logger = logging.getLogger(logger_name)
logger.setLevel(TCMConstants.LOG_LEVEL)

def main():
        fh = logging.handlers.TimedRotatingFileHandler(
		TCMConstants.LOG_PATH + logger_name + TCMConstants.LOG_EXTENSION,
		when=TCMConstants.WHEN, interval=TCMConstants.INTERVAL,
		backupCount=TCMConstants.BACKUP_COUNT)
	fh.setLevel(TCMConstants.LOG_LEVEL)
	formatter = logging.Formatter(TCMConstants.LOG_FORMAT)
	fh.setFormatter(formatter)
	logger.addHandler(fh)
	logger.info("Starting up")

	signal.signal(signal.SIGINT, exit_gracefully)
	signal.signal(signal.SIGTERM, exit_gracefully)

	if not have_required_permissions():
		logger.error("Missing some required permissions, exiting")
		exit_gracefully(TCMConstants.SPECIAL_EXIT_CODE, None)

	while True:
		for directory in next(os.walk(SOURCE_PATH))[1]:
			if os.listdir("{0}{1}".format(SOURCE_PATH, directory)):
				logger.debug("Directory {0}{1} not empty, skipping".format(
					SOURCE_PATH, directory))
			else:
				remove_empty_old_directory(SOURCE_PATH, directory)

		for path in VIDEO_PATHS:
			for file in os.listdir(path):
				remove_old_file(path, file)

		Stats.generate_stats_image()

		time.sleep(TCMConstants.SLEEP_DURATION)

### Startup functions ###

def have_required_permissions():
	have_perms = True
	for path in VIDEO_PATHS:
		have_perms = have_perms and TCMConstants.check_permissions(
			path, True, logger)
	return have_perms and TCMConstants.check_permissions(
		SOURCE_PATH, True, logger)

def exit_gracefully(signum, frame):
	logger.info("Received signal number {0}, exiting.".format(signum))
	exit(signum)

### Loop functions ###

def remove_empty_old_directory(path, name):
	if is_old_enough(name):
		logger.info("Removing empty directory: {0}{1}".format(path, name))
		try:
			os.rmdir("{0}{1}".format(path, name))
		except:
			logger.error("Error removing directory: {0}{1}".format(path, name))
	else:
		logger.debug("Directory {0}{1} is not ready for deletion, skipping".format(path, name))

def remove_old_file(path, file):
	if is_old_enough(extract_stamp(file)):
		logger.info("Removing old file: {0}{1}".format(path, file))
		try:
			os.remove("{0}{1}".format(path, file))
			pass
		except:
			logger.error("Error removing file: {0}{1}".format(path, file))
	else:
		logger.debug("File {0}{1} is not ready for deletion, skipping".format(path, file))

def extract_stamp(file):
	match = ALL_VIDEO_PATTERN.match(file)
	if match:
		logger.debug("Returning stamp {0} for file {1}".format(match.group(1)[:-1], file))
		return match.group(1)[:-1]
	else:
		logger.debug("No valid stamp found for file: {0}".format(file))
		return None

def is_old_enough(stamp_in_name):
	try:
		stamp = datetime.datetime.strptime(stamp_in_name, TCMConstants.FILENAME_TIMESTAMP_FORMAT)
		age = datetime.datetime.now() - stamp
		if age.days > TCMConstants.DAYS_TO_KEEP:
			return True
		else:
			return False
	except:
		logger.debug("Unrecognized name: {0}, skipping".format(stamp_in_name))
		return False

if __name__ == '__main__':
	main()
