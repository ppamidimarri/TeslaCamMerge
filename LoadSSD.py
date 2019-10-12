#!/usr/bin/env python3

# This script moves files placed in the "SHARE_PATH" location to the
# "RAW_FOLDER" locations under FOOTAGE_PATH and FOOTAGE_FOLDERS. I use
# it to pick up files placed in a CIFS share by teslausb and move them
# to a Samsung T5 SSD.

import os
import time
import shutil
import re
import TCMConstants

logger = TCMConstants.get_logger()

def main():
	if not have_required_permissions():
		logger.error("Missing some required permissions, exiting")
		TCMConstants.exit_gracefully(TCMConstants.SPECIAL_EXIT_CODE, None)

	while True:
		for folder in TCMConstants.FOOTAGE_FOLDERS:
			for root, dirs, files in os.walk("{0}{1}".format(TCMConstants.SHARE_PATH, folder), topdown=False):
				for name in files:
					if file_has_proper_name(name):
						move_file(os.path.join(root, name), folder)
					else:
						logger.warn("File '{0}' has invalid name, skipping".format(name))

		time.sleep(TCMConstants.SLEEP_DURATION)

### Startup functions ###

def have_required_permissions():
	retVal = True
	for folder in TCMConstants.FOOTAGE_FOLDERS:
		retVal = retVal and TCMConstants.check_permissions("{0}{1}".format(TCMConstants.SHARE_PATH, folder), True)
		retVal = retVal and TCMConstants.check_permissions("{0}{1}/{2}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.RAW_FOLDER), True)
	return retVal

### Loop functions ###

def move_file(file, folder):
	logger.info("Moving file {0}".format(file))
	if TCMConstants.check_file_for_read(file):
		try:
			shutil.move(file, "{0}{1}/{2}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.RAW_FOLDER))
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
