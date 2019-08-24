#!/usr/bin/env python3

# This script generates an image with statistics if STATS_FILENAME is set

import os
import time
import TCMConstants
import subprocess
import datetime
import re
import logging

logger = logging.getLogger(TCMConstants.get_basename())

def generate_stats_image():
	if TCMConstants.STATS_FILENAME:
		logger.debug("Generating stats in {0}".format(TCMConstants.STATS_FILENAME))
		footage_path, raw, fragment = TCMConstants.RAW_PATH.rsplit("/", 2)
		logger.debug("Footage root location: {0}".format(footage_path))
		with open("{0}/TeslaCamMerge/stats-template.html".format(TCMConstants.PROJECT_PATH), "r") as template:
			html = template.read()
			logger.debug("Read template:\n{0}".format(html))
			device, size, used, available, used_percentage, mount_point = get_disk_usage_details(footage_path)
			directory_table_rows = get_directory_table_rows(footage_path)
			timestamp = datetime.datetime.now().strftime(TCMConstants.STATS_TIMESTAMP_FORMAT)
			replacements = {
				"DEVICE" : device,
				"SIZE" : size,
				"USED" : used,
				"AVAILABLE" : available,
				"USED_PERCENTAGE" : used_percentage,
				"MOUNT_POINT" : mount_point,
				"DIRECTORY_TABLE_ROWS" : directory_table_rows,
				"TIMESTAMP" : timestamp,
				"DISK_COLOR" : get_disk_color(used_percentage)
			}
			output = ""
			for line in html.splitlines():
				output += do_replacements(line, replacements)
			logger.debug("HTML output:\n{0}".format(output))
			with open("{0}/{1}".format(footage_path, TCMConstants.STATS_FILENAME), "w+") as file:
				file.write(output)
		command = "export DISPLAY=:0 && {0} --url=file://{1}/{2} --out={1}/{3}".format(
			TCMConstants.CUTYCAPT_PATH, footage_path, TCMConstants.STATS_FILENAME, TCMConstants.STATS_IMAGE)
		logger.debug("Command: {0}".format(command))
		completed = subprocess.run(command, shell=True, stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		if completed.returncode == 0:
			logger.info("Updated stats image")
			try:
				os.remove("{0}/{1}".format(footage_path, TCMConstants.STATS_FILENAME))
			except:
				logger.error("Error removing: {0}/{1}".format(footage_path, TCMConstants.STATS_FILENAME))
		else:
			logger.error("Error running cutycapt command {0}, returncode: {3}, stdout: {1}, stderr: {2}".format(
				command, completed.stdout, completed.stderr, completed.returncode))

def get_disk_color(used_percentage):
	used = int(used_percentage[:-1])
	if used < 80:
		return "rgb(0, 255, 0);"
	elif used < 90:
		return "rgb(255, 255, 0);"
	else:
		return "rgb(255, 0, 0);"

def do_replacements(line, replacements):
        substrs = sorted(replacements, key=len, reverse=True)
        regexp = re.compile('|'.join(map(re.escape, substrs)))
        return regexp.sub(lambda match: replacements[match.group(0)], line)

def get_directory_table_rows(path):
	output = ""
	for item in os.listdir(path):
		if item == TCMConstants.STATS_FILENAME or item == TCMConstants.STATS_IMAGE:
			continue
		num_files, total_size = get_folder_details(path, item)
		output += "<tr><td>{0}</td><td class='number'>{1}</td><td class='number'>{2}</td></tr>".format(
			item, num_files, total_size)
	return output

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
	return "{0:-10d}".format(num_files), TCMConstants.convert_file_size(total_size)

def get_disk_usage_details(footage_path):
	command = "{0} -h {1}".format(TCMConstants.DF_PATH, footage_path)
	completed = subprocess.run(command, shell=True, stdin=subprocess.DEVNULL,
		stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	if completed.stderr or completed.returncode != 0:
		logger.error("Error running df command, returncode: {0}, stdout: {1}, stderr: {2}".format(
			completed.returncode, completed.stdout, completed.stderr))
		return None, None, None, None, None, None
	else:
		logger.debug("Disk space raw result:\n{0}".format(completed.stdout.decode("UTF-8")))
		line = completed.stdout.decode("UTF-8").splitlines()[1]
		return line[0:15].strip(), line[15:21].strip(), line[21:27].strip(), line[26:33].strip(), line[32:38].strip(), line[37:].strip()
