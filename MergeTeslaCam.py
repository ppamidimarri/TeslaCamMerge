#!/usr/bin/env python3

# This script users ffmpeg to generate combined videos of TeslaCam footage.
# It looks for files at "RAW_PATH" and waits for all (front, left-repeater,
# right-repeater) are available for a single timestamp. Once all three files
# are available, it merges them into one "full" file. It then creates a
# sped-up view of the "full" file as the "fast" file.

import os
import time
import subprocess
import datetime
import TCMConstants
import re
import logging

# ffmpeg commands and filters
ffmpeg_base = "{0} -hide_banner -loglevel error -timelimit {1}".format(
	TCMConstants.FFMPEG_PATH, TCMConstants.FFMPEG_TIMELIMIT)
ffmpeg_mid_full = f'-filter_complex "[1:v]scale=w={TCMConstants.FRONT_WIDTH}:h={TCMConstants.FRONT_HEIGHT}[top];[0:v]scale=w={TCMConstants.REST_WIDTH}:h={TCMConstants.REST_HEIGHT}[right];[3:v]scale=w={TCMConstants.REST_WIDTH}:h={TCMConstants.REST_HEIGHT}[back];[2:v]scale=w={TCMConstants.REST_WIDTH}:h={TCMConstants.REST_HEIGHT}[left];[left][back][right]hstack=inputs=3[bottom];[top][bottom]vstack=inputs=2[full];[full]drawtext=text=\''
ffmpeg_end_full = '\':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2" -movflags +faststart -threads 0'
ffmpeg_end_fast = '-vf "setpts=0.09*PTS" -c:v libx264 -crf 28 -profile:v main -tune fastdecode -movflags +faststart -threads 0'
ffmpeg_error_regex = '(.*): Invalid data found when processing input'
ffmpeg_error_pattern = re.compile(ffmpeg_error_regex)

logger = TCMConstants.get_logger()

def main():
	if not have_required_permissions():
		logger.error("Missing some required permissions, exiting")
		TCMConstants.exit_gracefully(TCMConstants.SPECIAL_EXIT_CODE, None)

	while True:
		logger.debug("Starting new iteration")
		for folder in TCMConstants.FOOTAGE_FOLDERS:
			raw_files = os.listdir("{0}{1}/{2}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.RAW_FOLDER))
			for file in raw_files:
				logger.debug("Starting with file {0}".format(file))
				try:
					stamp, camera = file.rsplit("-", 1)
				except ValueError:
					if file != TCMConstants.BAD_VIDEOS_FILENAME and file != TCMConstants.BAD_SIZES_FILENAME:
						logger.warn("Unrecognized filename: {0}".format(file))
					continue
				process_stamp(stamp, folder)

		time.sleep(TCMConstants.SLEEP_DURATION)

### Startup functions ###

def have_required_permissions():
	retVal = True
	for folder in TCMConstants.FOOTAGE_FOLDERS:
		retVal = retVal and TCMConstants.check_permissions("{0}{1}/{2}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.RAW_FOLDER), False)
		retVal = retVal and TCMConstants.check_permissions("{0}{1}/{2}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.FULL_FOLDER), True)
		retVal = retVal and TCMConstants.check_permissions("{0}{1}/{2}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.FAST_FOLDER), True)
	return retVal

### Loop functions ###

def process_stamp(stamp, folder):
	logger.debug("Processing stamp {0} in {1}".format(stamp, folder))
	if stamp_is_all_ready(stamp, folder):
		logger.debug("Stamp {0} in {1} is ready to go".format(stamp, folder))
		if TCMConstants.check_file_for_write("{0}{1}/{2}/{3}-{4}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.FULL_FOLDER, stamp, TCMConstants.FULL_TEXT)):
			run_ffmpeg_command("Merge", folder, stamp, 0)
		else:
			logger.debug("Full file exists for stamp {0}".format(stamp))
		if TCMConstants.check_file_for_read("{0}{1}/{2}/{3}-{4}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.FULL_FOLDER, stamp, TCMConstants.FULL_TEXT)):
			if TCMConstants.check_file_for_write("{0}{1}/{2}/{3}-{4}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.FAST_FOLDER, stamp, TCMConstants.FAST_TEXT)):
				run_ffmpeg_command("Fast preview", folder, stamp, 1)
			else:
				logger.debug("Fast file exists for stamp {0} at {1}".format(stamp, folder))
		else:
			logger.warn("Full file {0}{1}/{2}/{3}-{4} not ready for read, postponing fast preview".format(
				TCMConstants.FOOTAGE_PATH, folder, TCMConstants.FULL_FOLDER, stamp, TCMConstants.FULL_TEXT))
	else:
		logger.debug("Stamp {0} not yet ready in {1}".format(stamp, folder))

def stamp_is_all_ready(stamp, folder):
	front_file = "{0}{1}/{2}/{3}-{4}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.RAW_FOLDER, stamp, TCMConstants.FRONT_TEXT)
	left_file = "{0}{1}/{2}/{3}-{4}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.RAW_FOLDER, stamp, TCMConstants.LEFT_TEXT)
	right_file = "{0}{1}/{2}/{3}-{4}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.RAW_FOLDER, stamp, TCMConstants.RIGHT_TEXT)
	back_file = "{0}{1}/{2}/{3}-{4}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.RAW_FOLDER, stamp, TCMConstants.BACK_TEXT)
	if TCMConstants.check_file_for_read(front_file) and TCMConstants.check_file_for_read(left_file) and TCMConstants.check_file_for_read(right_file) and TCMConstants.check_file_for_read(back_file) and file_sizes_in_same_range(folder, stamp, front_file, left_file, right_file, back_file):
		return True
	else:
		return False

def file_sizes_in_same_range(folder, stamp, front_file, left_file, right_file, back_file):
	front_size = os.path.getsize(front_file)
	left_size = os.path.getsize(left_file)
	right_size = os.path.getsize(right_file)
	back_size = os.path.getsize(back_file)
	if front_size == 0 or left_size == 0 or right_size == 0 or back_size == 0:
		add_to_bad_sizes(
			folder, stamp, TCMConstants.convert_file_size(front_size),
			TCMConstants.convert_file_size(left_size),
			TCMConstants.convert_file_size(right_size),
			TCMConstants.convert_file_size(back_size))
		return False
	else:
		if abs((front_size - left_size) / front_size) > TCMConstants.SIZE_RANGE or abs((front_size - right_size) / front_size) > TCMConstants.SIZE_RANGE or abs((left_size - right_size) / left_size) > TCMConstants.SIZE_RANGE or abs((front_size - back_size) / front_size) > TCMConstants.SIZE_RANGE or abs((left_size - back_size) / left_size) > TCMConstants.SIZE_RANGE or abs((right_size - back_size) / right_size) > TCMConstants.SIZE_RANGE:
			add_to_bad_sizes(
				folder, stamp, TCMConstants.convert_file_size(front_size),
				TCMConstants.convert_file_size(left_size),
				TCMConstants.convert_file_size(right_size),
				TCMConstants.convert_file_size(back_size))
			return False
		else:
			return True

### FFMPEG command functions ###

def run_ffmpeg_command(log_text, folder, stamp, video_type):
	logger.info("{0} started in {2}: {1}...".format(log_text, stamp, folder))
	command = get_ffmpeg_command(folder, stamp, video_type)
	logger.debug("Command: {0}".format(command))
	completed = subprocess.run(command, shell=True,
		stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
		stderr=subprocess.PIPE)
	if completed.stderr or completed.returncode != 0:
		logger.error("Error running ffmpeg command: {0}, returncode: {3}, stdout: {1}, stderr: {2}".format(
			command, completed.stdout, completed.stderr, completed.returncode))
		for line in completed.stderr.decode("UTF-8").splitlines():
			match = ffmpeg_error_pattern.match(line)
			if match:
				file = match.group(1)
				if video_type == 1:
					logger.debug("Will try to remove bad merged file: {0}".format(file))
					try:
						os.remove(file)
					except:
						logger.warn("Failed to remove bad file: {0}".format(file))
				else:
					add_to_bad_videos(file)
	else:
		logger.debug("FFMPEG stdout: {0}, stderr: {1}".format(
			completed.stdout, completed.stderr))
	logger.info("{0} completed: {1}.".format(log_text, stamp))

def get_ffmpeg_command(folder, stamp, video_type):
	if video_type == 0:
		command = "{0} -i {1}{2}/{3}/{4}-{5} -i {1}{2}/{3}/{4}-{6} -i {1}{2}/{3}/{4}-{7} -i {1}{2}/{3}/{4}-{8} {9}{10}{11} {1}{2}/{12}/{4}-{13}".format(
			ffmpeg_base, TCMConstants.FOOTAGE_PATH, folder, TCMConstants.RAW_FOLDER, stamp, TCMConstants.RIGHT_TEXT,
			TCMConstants.FRONT_TEXT, TCMConstants.LEFT_TEXT, TCMConstants.BACK_TEXT, ffmpeg_mid_full,
			format_timestamp(stamp), ffmpeg_end_full, TCMConstants.FULL_FOLDER, TCMConstants.FULL_TEXT)
	elif video_type == 1:
		command = "{0} -i {1}{2}/{3}/{4}-{5} {6} {1}{2}/{7}/{4}-{8}".format(
			ffmpeg_base, TCMConstants.FOOTAGE_PATH, folder, TCMConstants.FULL_FOLDER, stamp, TCMConstants.FULL_TEXT, ffmpeg_end_fast,
			TCMConstants.FAST_FOLDER, TCMConstants.FAST_TEXT)
	else:
		logger.error("Unrecognized video type {0} for {1} in {2}".format(video_type, stamp, folder))
	return command

def add_to_bad_videos(folder, name):
	simple_name = name.replace("{0}{1}/{2}/".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.RAW_FOLDER), '')
	add_string_to_sorted_file(
		"{0}{1}/{2}/{3}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.RAW_FOLDER, TCMConstants.BAD_VIDEOS_FILENAME),
		simple_name, "{0}\n".format(simple_name),
		"Skipping over bad source file: {0}".format(name),
		logging.DEBUG)

def add_to_bad_sizes(folder, stamp, front, left, right, back):
	add_string_to_sorted_file(
		"{0}{1}/{2}/{3}".format(TCMConstants.FOOTAGE_PATH, folder, TCMConstants.RAW_FOLDER, TCMConstants.BAD_SIZES_FILENAME),
		stamp,
		"{0}: Front {1}, Left {2}, Right {3}, Back: {4}\n".format(
			stamp, front, left, right, back),
		"Size issue at {0}: Front {1}, Left {2}, Right {3}, Back: {4}".format(
			stamp, front, left, right, back),
		logging.WARN)

### Other utility functions ###

def add_string_to_sorted_file(name, key, string, log_message, log_level):
	files = []
	if os.path.isfile(name):
		with open(name, "r") as file:
			files = file.readlines()
			for line in files:
				if key in line:
					return
	files.append(string)
	with open(name, "w+") as writer:
		outlist = sorted(files)
		logger.log(log_level, log_message)
		for line in outlist:
			writer.write(line)

def format_timestamp(stamp):
	timestamp = datetime.datetime.strptime(stamp, TCMConstants.FILENAME_TIMESTAMP_FORMAT)
	logger.debug("Timestamp: {0}".format(timestamp))
	return timestamp.strftime(TCMConstants.WATERMARK_TIMESTAMP_FORMAT)

if __name__ == '__main__':
	main()
