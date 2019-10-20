#!/usr/bin/env python3

# This script generates an image with statistics if STATS_FILENAME is set

import os
import time
import TCMConstants
import subprocess
import datetime
import re
import logging

def generate_stats_image():
	logger = logging.getLogger(TCMConstants.get_basename())
	if TCMConstants.STATS_FILENAME:
		logger.debug(f"Generating stats in {TCMConstants.STATS_FILENAME}")
		logger.debug(f"Footage root location: {TCMConstants.FOOTAGE_PATH}")
		with open(f"{TCMConstants.PROJECT_PATH}/TeslaCamMerge/stats-template.html", "r") as template:
			html = template.read()
			logger.debug(f"Read template:\n{html}")
			device, size, used, available, used_percentage, mount_point = get_disk_usage_details(TCMConstants.FOOTAGE_PATH)
			directory_table_rows = get_directory_table_rows(TCMConstants.FOOTAGE_PATH)
			service_table_rows = get_service_table_rows()
			timestamp = datetime.datetime.now().strftime(TCMConstants.STATS_TIMESTAMP_FORMAT)
			replacements = {
				"DEVICE" : device,
				"SIZE" : size,
				"USED" : used,
				"AVAILABLE" : available,
				"USED_PERCENTAGE" : used_percentage,
				"MOUNT_POINT" : mount_point,
				"DIRECTORY_TABLE_ROWS" : directory_table_rows,
				"SERVICE_TABLE_ROWS" : service_table_rows,
				"TIMESTAMP" : timestamp,
				"DISK_COLOR" : get_disk_color(used_percentage)
			}
			output = ""
			for line in html.splitlines():
				output += do_replacements(line, replacements)
			logger.debug(f"HTML output:\n{output}")
			with open(f"{TCMConstants.FOOTAGE_PATH}/{TCMConstants.STATS_FILENAME}", "w+") as file:
				file.write(output)
		command = f'{TCMConstants.XVFB_RUN_PATH} --server-args="-screen 0, 1280x1200x24" {TCMConstants.CUTYCAPT_PATH} --url=file://{TCMConstants.FOOTAGE_PATH}/{TCMConstants.STATS_FILENAME} --out={TCMConstants.FOOTAGE_PATH}/{TCMConstants.STATS_IMAGE}'
		logger.debug(f"Command: {command}")
		completed = subprocess.run(command, shell=True, stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		if completed.returncode == 0:
			logger.info("Updated stats image")
			try:
				os.remove(f"{TCMConstants.FOOTAGE_PATH}/{TCMConstants.STATS_FILENAME}")
			except:
				logger.error(f"Error removing: {TCMConstants.FOOTAGE_PATH}/{TCMConstants.STATS_FILENAME}")
		else:
			logger.error(f"Error running cutycapt command {command}, returncode: {completed.returncode}, stdout: {completed.stdout}, stderr: {completed.stderr}")

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
		output += f"<tr><td>{item}</td><td class='number'>{num_files:,d}</td><td class='number'>{total_size}</td></tr>"
		if TCMConstants.MULTI_CAR and item in TCMConstants.CAR_LIST and num_files > 0:
			for folder in TCMConstants.FOOTAGE_FOLDERS:
				sub_files, sub_size = get_folder_details(f"{path}/{item}", folder)
				output += f"<tr><td class='small'>&nbsp;&nbsp;{folder}</td><td class='smallnumber'>{sub_files:,d}</td><td class='smallnumber'>{sub_size}</td></tr>"
				if sub_files > 0:
					output += get_subdirectory_table_rows(f"{path}/{item}/{folder}", "&nbsp;&nbsp;&nbsp;&nbsp;", "smaller")
		else:
			if item in TCMConstants.FOOTAGE_FOLDERS and num_files > 0:
				output += get_subdirectory_table_rows(f"{path}/{item}", "&nbsp;&nbsp;", "small")
	return output

def get_subdirectory_table_rows(path, indent, font_class):
	output = ""
	raw_files, raw_size = get_folder_details(path, TCMConstants.RAW_FOLDER)
	output += f"<tr><td class='{font_class}'>{indent}{TCMConstants.RAW_FOLDER}</td><td class='{font_class}number'>{raw_files:,d}</td><td class='{font_class}number'>{raw_size}</td></tr>"
	full_files, full_size = get_folder_details(path, TCMConstants.FULL_FOLDER)
	output += f"<tr><td class='{font_class}'>{indent}{TCMConstants.FULL_FOLDER}</td><td class='{font_class}number'>{full_files:,d}</td><td class='{font_class}number'>{full_size}</td></tr>"
	fast_files, fast_size = get_folder_details(path, TCMConstants.FAST_FOLDER)
	output += f"<tr><td class='{font_class}'>{indent}{TCMConstants.FULL_FOLDER}</td><td class='{font_class}number'>{fast_files:,d}</td><td class='{font_class}number'>{fast_size}</td></tr>"
	return output

def get_service_table_rows():
	command = f"{TCMConstants.SYSTEMCTL_PATH} show -p Id -p Name -p SubState --value tcm-*"
	output = get_service_details(command)
	creds = ""
	try:
		import DownloadTC
		creds = DownloadTC.SERVER_CREDENTIALS
	except:
		logging.getLogger(TCMConstants.get_basename()).debug("No TCM2ndHome connected")
	if creds:
		command = f"{TCMConstants.SYSTEMCTL_PATH} show -p Id -p Name -p SubState --value tcm2-* -H {creds}"
		output += get_service_details(command)
	return output

def get_service_details(command):
	output = ""
	completed = subprocess.run(command, shell=True, stdin=subprocess.DEVNULL,
		stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	if completed.stderr or completed.returncode != 0:
		logging.getLogger(TCMConstants.get_basename()).error(
			f"Error running systemctl command, returncode: {completed.returncode}, stdout: {completed.stdout}, stderr: {completed.stderr}")
	else:
		lines = completed.stdout.splitlines()
		i = 0
		while i < len(lines):
			if i % 3 == 0:
				name = lines[i].decode("UTF-8").split(".")[0]
				service_class = ""
				if lines[i+1].decode("UTF-8") == "running":
					service_class = "servicerunning"
				else:
					service_class = "servicedead"
				output += f"<tr><td class='{service_class}'>{name}</td></tr>"
			i += 1
	return output

def get_folder_details(path, file):
	total_size = 0
	num_files = 0
	for dirpath, dirnames, filenames in os.walk(f"{path}/{file}"):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			# Skip symbolic links
			if not os.path.islink(fp):
				total_size += os.path.getsize(fp)
				num_files += 1
	return num_files, TCMConstants.convert_file_size(total_size)

def get_disk_usage_details(footage_path):
	logger = logging.getLogger(TCMConstants.get_basename())
	command = f"{TCMConstants.DF_PATH} -h {footage_path}"
	completed = subprocess.run(command, shell=True, stdin=subprocess.DEVNULL,
		stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	if completed.stderr or completed.returncode != 0:
		logger.error(f"Error running df command, returncode: {completed.returncode}, stdout: {completed.stdout}, stderr: {completed.stderr}")
		return None, None, None, None, None, None
	else:
		logger.debug("Disk space raw result:\n{0}".format(completed.stdout.decode("UTF-8")))
		line = completed.stdout.decode("UTF-8").splitlines()[1]
		return re.split("\s+", line)
