#!/usr/bin/env python3

# This script moves files placed in the "source" location to the
# "destination" location. I use it to pick up files placed in a
# CIFS share by teslausb and move them to a Samsung T5 SSD.

import inotify.adapters
import shutil
import signal
import logging

logger_name = 'LoadSSD'
source_path = '/samba/fjnuser/'
destination_path = '/media/pavan/Samsung_T5/Footage/Raw/'

def main():
	logging.getLogger(logger_name).setLevel(logging.DEBUG)
	fh = logging.FileHandler('/home/pavan/log/LoadSSD.log')
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
		return

	for event in i.event_gen(yield_nones = False):
		(_, type_names, path, filename) = event
		move_file(filename)

def move_file(filename):
	logging.getLogger(logger_name).info("Moving file {0}".format(filename))
	try:
		shutil.move(source_path + filename, destination_path)
		logging.getLogger(logger_name).debug("Moved file {0}".format(filename))
	except:
		logging.getLogger(logger_name).warn("Failed to move {0}".format(filename))

def exit_gracefully(signum, frame):
	logging.getLogger(logger_name).info("Received signal number {0}, exiting.".format(signum))
	exit()

if __name__ == '__main__':
	main()
