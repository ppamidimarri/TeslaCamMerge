#!/usr/bin/env python3

# This script generates a text file with statistics if STATS_FILENAME is set

import os
import time
import logging
import TCMConstants
import subprocess
import datetime

logger_name = 'Stats'
logger = logging.getLogger(logger_name)
logger.setLevel(TCMConstants.LOG_LEVEL)
fh = logging.FileHandler(TCMConstants.LOG_PATH + logger_name + TCMConstants.LOG_EXTENSION)
fh.setLevel(TCMConstants.LOG_LEVEL)
formatter = logging.Formatter(TCMConstants.LOG_FORMAT)
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.info("Starting up")

def generate_stats():
	if TCMConstants.STATS_FILENAME and datetime.datetime.now().minute in TCMConstants.STATS_FREQUENCY:
		logger.debug("Generating stats in {0}".format(TCMConstants.STATS_FILENAME))
		footage_path, raw, fragment = TCMConstants.RAW_PATH.rsplit("/", 2)
		logger.debug("Footage root location: {0}".format(footage_path))
		folders_table = get_folders_table(footage_path)
		disk_usage = get_disk_usage(footage_path)
		content = "Footage Details\n{0}\n\nDisk Space Details\n{1}\n\nGenerated at {2}\n".format(
			folders_table, disk_usage,
			datetime.datetime.now().strftime(TCMConstants.STATS_TIMESTAMP_FORMAT))
		with open("{0}/{1}".format(footage_path, TCMConstants.STATS_FILENAME), "w+") as file:
			logger.debug("Writing content to file:\n{0}".format(content))
			file.write(content)
			logger.info("Updated stats")

def get_folders_table(footage_path):
	result =  "----------------------------------\n"
	result += " Folder    | # of Files |    Size \n"
	result += "----------------------------------\n"
	for item in os.listdir(footage_path):
		if item == TCMConstants.STATS_FILENAME:
			continue
		num_files, total_size = get_folder_details(footage_path, item)
		result += " {0:9} | {1} | {2} \n".format(
			item, num_files, total_size)
	result += "----------------------------------\n"
	logger.debug("Folders result:\n{0}".format(result))
	return result

def get_folder_details(path, file):
	total_size = 0
	num_files = 0
	for dirpath, dirnames, filenames in os.walk("{0}/{1}".format(path, file)):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			# Skip symbolic links
			if not os.path.islink(fp):
				total_size += os.path.getsize(fp)
				num_files += 1
	return "{0:-10d}".format(num_files), convert_file_size(total_size)

def convert_file_size(size):
	if size <= 1024:
		return "{0:-6d}B".format(size)
	elif size <= 1024*1024:
		return "{0:-6.1f}K".format(size/1024)
	elif size <= 1024*1024*1024:
		return "{0:-6.1f}M".format(size/(1024*1024))
	elif size <= 1024*1024*1024*1024:
		return "{0:-6.1f}G".format(size/(1024*1024*1024))
	else:
		return "{0:-6.1f}G".format(size/(1024*1024*1024))

def get_disk_usage(footage_path):
	command = "{0} -h {1}".format(TCMConstants.DF_PATH, footage_path)
	result = ""
	completed = subprocess.run(command, shell=True, stdin=subprocess.DEVNULL,
		stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	if completed.stderr or completed.returncode != 0:
		logger.error("Error running df command, returncode: {0}, stdout: {1}, stderr: {2}".format(
			completed.returncode, completed.stdout, completed.stderr))
		result += "----------------------------------------------------------\n"
		result += "Disk space usage numbers are unavailable at the moment"
	else:
		logger.debug("Disk space raw result:\n{0}".format(completed.stdout.decode("UTF-8")))
		for line in completed.stdout.decode("UTF-8").splitlines():
			result += "----------------------------------------------------------\n"
			result += " {0}|{1}|{2}|{3}|{4}|{5} \n".format(
				line[0:15], line[15:21], line[21:27], line[26:33], line[32:38], line[37:])
		result += "----------------------------------------------------------\n"
		logger.debug("Disk space formatted result:\n{0}".format(result))
	return result
