#!/usr/bin/env python3

# This script moves files placed in the "SHARE_PATH" location to the
# "RAW_PATH" location. I use it to pick up files placed in a
# CIFS share by teslausb and move them to a Samsung T5 SSD.

import inotify.adapters
import shutil
import signal
import logging
import TCMConstants

logger_name = 'LoadSSD'
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

	i = inotify.adapters.Inotify()

	try:
		i.add_watch(TCMConstants.SHARE_PATH,
			inotify.constants.IN_CLOSE_WRITE)
		logger.debug("Added watch for {0}".format(TCMConstants.SHARE_PATH))
	except:
		logger.error("Failed to add watch for {0}, exiting".format(TCMConstants.SHARE_PATH))
		exit_gracefully(TCMConstants.SPECIAL_EXIT_CODE, None)

	for event in i.event_gen(yield_nones = False):
		(_, type_names, path, filename) = event
		move_file(filename)

def move_file(filename):
	logger.info("Moving file {0}".format(filename))
	try:
		shutil.move(TCMConstants.SHARE_PATH + filename, TCMConstants.RAW_PATH)
		logger.debug("Moved file {0}".format(filename))
	except:
		logger.warn("Failed to move {0}".format(filename))

def exit_gracefully(signum, frame):
	logger.info("Received signal number {0}, exiting.".format(signum))
	exit(signum)

if __name__ == '__main__':
	main()
