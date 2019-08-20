#!/usr/bin/env python3

# This script moves files placed in the "SHARE_PATH" location to the
# "RAW_PATH" location. I use it to pick up files placed in a
# CIFS share by teslausb and move them to a Samsung T5 SSD.

import os
import time
import shutil
import signal
import re
import TCMConstants

logger = TCMConstants.get_logger('LoadSSD')

def main():
	signal.signal(signal.SIGINT, TCMConstants.exit_gracefully)
	signal.signal(signal.SIGTERM, TCMConstants.exit_gracefully)

	if not have_required_permissions():
		logger.error("Missing some required permissions, exiting")
		TCMConstants.exit_gracefully(TCMConstants.SPECIAL_EXIT_CODE, None)

	while True:
		for root, dirs, files in os.walk(TCMConstants.SHARE_PATH, topdown=False):
			for name in files:
				if file_has_proper_name(name):
					move_file(os.path.join(root, name))
				else:
					logger.warn("File '{0}' has invalid name, skipping".format(name))

		time.sleep(TCMConstants.SLEEP_DURATION)

### Startup functions ###

def have_required_permissions():
	return TCMConstants.check_permissions(
		TCMConstants.SHARE_PATH, True, logger) and TCMConstants.check_permissions(
		TCMConstants.RAW_PATH, True, logger)

### Loop functions ###

def move_file(file):
	logger.info("Moving file {0}".format(file))
	if TCMConstants.check_file_for_read(file, logger):
		try:
			shutil.move(file, TCMConstants.RAW_PATH)
			logger.debug("Moved file {0}".format(file))
		except:
			logger.error("Failed to move {0}".format(file))
	else:
		logger.debug("File {0} still being written, skipping for now".format(file))

def file_has_proper_name(file):
	if TCMConstants.FILENAME_PATTERN.match(file):
		return True
	else:
		return False

if __name__ == '__main__':
	main()
