#!/usr/bin/env python3

# This script uploads files placed in UPLOAD_LOCAL_PATH on the
# computer to the UPLOAD_REMOTE_PATH location using rclone.

import os
import time
import subprocess
import signal
import logging
import TCMConstants

logger_name = 'UploadDrive'
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

	files = []
	while True:
		try:
			files = os.listdir(TCMConstants.UPLOAD_LOCAL_PATH)
		except:
			logger.error("Error listing directory {0}".format(TCMConstants.UPLOAD_LOCAL_PATH))
			exit_gracefully(TCMConstants.SPECIAL_EXIT_CODE)

		for file in files:
			upload_file(file)
		time.sleep(60)

def upload_file(filename):
	logger.info("Uploading file {0}".format(filename))

	command = "{0} move {1}{2} {3}".format(
		TCMConstants.RCLONE_PATH, TCMConstants.UPLOAD_LOCAL_PATH,
		filename, TCMConstants.UPLOAD_REMOTE_PATH)
	logger.debug("Command: {0}".format(command))
	try:
		subprocess.run(command, shell=True, stdin=subprocess.DEVNULL)
		logger.info("Uploaded file {0}".format(filename))
	except shutil.Error:
		logger.warn("Failed to upload {0}".format(filename))

def exit_gracefully(signum, frame):
	logger.info("Received signal number {0}, exiting.".format(signum))
	exit(signum)

if __name__ == '__main__':
	main()
