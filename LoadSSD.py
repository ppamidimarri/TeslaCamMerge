#!/usr/bin/env python3

# This script moves files placed in the "SHARE_PATHS" locations to the
# "RAW_FOLDER" locations under FOOTAGE_PATH and FOOTAGE_FOLDERS for all
# cars in CAR_LIST. I use it to pick up files placed in a CIFS share by
# teslausb and move them to a location for merging and viewing.

import os
import time
import shutil
import re
import TCMConstants

logger = TCMConstants.get_logger()

def main():
	if len(TCMConstants.SHARE_PATHS) <= 0:
		logger.error("No share paths defined, please fix in TCMConstants.py and restart.")
		TCMConstants.exit_gracefully(TCMConstants.SPECIAL_EXIT_CODE, None)
	if not have_required_permissions():
		logger.error("Missing some required permissions, exiting")
		TCMConstants.exit_gracefully(TCMConstants.SPECIAL_EXIT_CODE, None)

	while True:
		for index, share in enumerate(TCMConstants.SHARE_PATHS):
			for folder in TCMConstants.FOOTAGE_FOLDERS:
				for root, dirs, files in os.walk(f"{share}{folder}", topdown=False):
					for name in files:
						if file_has_proper_name(name):
							sub_path = folder
							if TCMConstants.MULTI_CAR:
								sub_path = f"{TCMConstants.CAR_LIST[index]}/{folder}"
							move_file(os.path.join(root, name), sub_path)
						else:
							logger.warn(f"File '{name}' has invalid name, skipping")

		time.sleep(TCMConstants.SLEEP_DURATION)

### Startup functions ###

def have_required_permissions():
	have_perms = True
	for index, share in enumerate(TCMConstants.SHARE_PATHS):
		for folder in TCMConstants.FOOTAGE_FOLDERS:
			have_perms = have_perms and TCMConstants.check_permissions(f"{share}{folder}", True)
			sub_path = folder
			if TCMConstants.MULTI_CAR:
				sub_path = f"{TCMConstants.CAR_LIST[index]}/{folder}"
			have_perms = have_perms and TCMConstants.check_permissions(
				f"{TCMConstants.FOOTAGE_PATH}{sub_path}/{TCMConstants.RAW_FOLDER}", True)
	return have_perms

### Loop functions ###

def move_file(file, folder):
	logger.info(f"Moving file {file} into {folder}")
	if TCMConstants.check_file_for_read(file):
		try:
			shutil.move(file, f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.RAW_FOLDER}")
			logger.debug(f"Moved file {file} into {folder}")
		except:
			logger.error(f"Failed to move {file} into {folder}")
	else:
		logger.debug(f"File {file} still being written, skipping for now")

def file_has_proper_name(file):
	if TCMConstants.FILENAME_PATTERN.match(file):
		return True
	else:
		return False

if __name__ == '__main__':
	main()
