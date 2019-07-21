#!/usr/bin/env python3

# This script uploads files placed in "source_path" directory on the
# computer to the "destination_path" location using rclone.

import inotify.adapters
import subprocess
import signal
import logging

logger_name = 'UploadDrive'
source_path = '/media/pavan/Samsung_T5/Footage/Upload/'
destination_path = 'gdrive:/TeslaCam'

def main():
	logging.getLogger(logger_name).setLevel(logging.DEBUG)
	fh = logging.FileHandler('/home/pavan/log/UploadDrive.log')
	fh.setLevel(logging.INFO)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	fh.setFormatter(formatter)
	logging.getLogger(logger_name).addHandler(fh)
	logging.getLogger(logger_name).info("Starting up")

	signal.signal(signal.SIGINT, exit_gracefully)
	signal.signal(signal.SIGTERM, exit_gracefully)

	i = inotify.adapters.Inotify()

	try:
		i.add_watch(source_path,
			inotify.constants.IN_CLOSE_WRITE)
		logging.getLogger(logger_name).debug(
			"Added watch for {0}".format(source_path))
	except:
		logging.getLogger(logger_name).error(
			"Failed to add watch for {0}".format(source_path))

	for event in i.event_gen(yield_nones = False):
		(_, type_names, path, filename) = event
		upload_file(filename)

def upload_file(filename):
	logging.getLogger(logger_name).info("Uploading file {0}".format(filename))

	command = '/usr/local/bin/rclone move ' + source_path + filename + ' ' + destination_path
	logging.getLogger(logger_name).debug("Command: {0}".format(command))
	try:
		subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		logging.getLogger(logger_name).info("Uploaded file {0}".format(filename))
	except shutil.Error:
		logging.getLogger(logger_name).warn("Failed to upload {0}".format(filename))

def exit_gracefully(signum, frame):
	logging.getLogger(logger_name).info("Received signal number {0}, exiting.".format(signum))
	exit()

if __name__ == '__main__':
	main()
