#!/usr/bin/env python3

# This script uploads files placed in UPLOAD_LOCAL_PATH on the
# computer to the UPLOAD_REMOTE_PATH location using rclone.

import os
import time
import subprocess
import TCMConstants

logger = TCMConstants.get_logger()

def main():
	files = []
	while True:
		try:
			files = os.listdir(TCMConstants.UPLOAD_LOCAL_PATH)
		except:
			logger.error("Error listing directory {0}".format(TCMConstants.UPLOAD_LOCAL_PATH))
			TCMConstants.exit_gracefully(TCMConstants.SPECIAL_EXIT_CODE)

		for file in files:
			upload_file(file)
		time.sleep(TCMConstants.SLEEP_DURATION)

def upload_file(filename):
	logger.info("Uploading file {0}".format(filename))

	command = "{0} move {1}{2} {3}".format(
		TCMConstants.RCLONE_PATH, TCMConstants.UPLOAD_LOCAL_PATH,
		filename, TCMConstants.UPLOAD_REMOTE_PATH)
	logger.debug("Command: {0}".format(command))
	try:
		completed = subprocess.run(command, shell=True, stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		if completed.stderr or completed.returncode != 0:
			logger.error("Error running rclone command: {0}, returncode: {3}, stdout: {1}, stderr: {2}".format(
				command, completed.stdout, completed.stderr, completed.returncode))
		else:
			logger.info("Uploaded file {0}".format(filename))
	except shutil.Error:
		logger.error("Failed to upload {0}".format(filename))

if __name__ == '__main__':
	main()
