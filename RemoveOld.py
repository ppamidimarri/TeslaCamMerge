#!/usr/bin/env python3

# This script removes empty directories under "SOURCE_PATH"
# whose names have a timestamp older than by "DAYS_TO_KEEP".

import os
import time
import shutil
import signal
import logging
import TCMConstants
import datetime

SOURCE_PATH = TCMConstants.SHARE_PATH

DAYS_TO_KEEP = 30

logger_name = 'RemoveOld'
logger = logging.getLogger(logger_name)
logger.setLevel(TCMConstants.LOG_LEVEL)

def main():
	fh = logging.FileHandler(TCMConstants.LOG_PATH + logger_name + TCMConstants.LOG_EXTENSION)
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
			if os.listdir("{0}/{1}".format(SOURCE_PATH, directory)):
				logger.debug("Directory {0}/{1} not empty, skipping".format(
					SOURCE_PATH, directory))
			else:
				remove_empty_directory(directory)

		time.sleep(TCMConstants.SLEEP_DURATION)

### Startup functions ###

def have_required_permissions():
	return TCMConstants.check_permissions(
		SOURCE_PATH, True, logger)

def exit_gracefully(signum, frame):
	logger.info("Received signal number {0}, exiting.".format(signum))
	exit(signum)

### Loop functions ###

def remove_empty_directory(name):
	if is_old_enough(name):
		logger.info("Removing empty directory: {0}".format(name))
		try:
			os.rmdir("{0}/{1}".format(SOURCE_PATH, name))
		except:
			logger.error("Error removing directory: {0}".format(name))
	else:
		logger.debug("Directory {0}/{1} is not ready for deletion, skipping".format(SOURCE_PATH, name))

def is_old_enough(name):
	try:
		stamp = datetime.datetime.strptime(name, TCMConstants.FILENAME_TIMESTAMP_FORMAT)
		age = datetime.datetime.now() - stamp
		if age.days > DAYS_TO_KEEP:
			return True
		else:
			return False
	except:
		logger.debug("Unrecognized directory name format: {0}/{1}, skipping".format(SOURCE_PATH, name))
		return False

if __name__ == '__main__':
	main()
