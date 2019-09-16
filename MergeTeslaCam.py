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
ffmpeg_mid_full = '-filter_complex "[1:v]scale=w=1.2*iw:h=1.2*ih[top];[0:v]scale=w=0.6*iw:h=0.6*ih[right];[2:v]scale=w=0.6*iw:h=0.6*ih[left];[left][right]hstack=inputs=2[bottom];[top][bottom]vstack=inputs=2[full];[full]drawtext=text=\''
ffmpeg_end_full = '\':fontcolor=white:fontsize=48:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2" -movflags +faststart -threads 0'
ffmpeg_end_fast = '-vf "setpts=0.09*PTS" -c:v libx264 -crf 28 -profile:v main -tune fastdecode -movflags +faststart -threads 0'
ffmpeg_error_regex = '(.*): Invalid data found when processing input'
ffmpeg_error_pattern = re.compile(ffmpeg_error_regex)

logger = TCMConstants.get_logger()

def main():
	if not have_required_permissions():
		logger.error("Missing some required permissions, exiting")
		TCMConstants.exit_gracefully(TCMConstants.SPECIAL_EXIT_CODE, None)

	while True:
		logger.info("Starting new iteration")
		raw_files = os.listdir(TCMConstants.RAW_PATH)
		for file in raw_files:
			logger.debug("Starting with file {0}".format(file))
			try:
				stamp, camera = file.rsplit("-", 1)
			except ValueError:
				if file != TCMConstants.BAD_VIDEOS_FILENAME and file != TCMConstants.BAD_SIZES_FILENAME:
					logger.warn("Unrecognized filename: {0}".format(file))
				continue
			process_stamp(stamp)

		time.sleep(TCMConstants.SLEEP_DURATION)

### Startup functions ###

def have_required_permissions():
	return TCMConstants.check_permissions(
		TCMConstants.RAW_PATH, False) and TCMConstants.check_permissions(
		TCMConstants.FULL_PATH, True) and TCMConstants.check_permissions(
		TCMConstants.FAST_PATH, True)

### Loop functions ###

def process_stamp(stamp):
	logger.debug("Processing stamp {0}".format(stamp))
	if stamp_is_all_ready(stamp):
		logger.debug("Stamp {0} is ready to go".format(stamp))
		if TCMConstants.check_file_for_write("{0}{1}-{2}".format(TCMConstants.FULL_PATH, stamp, TCMConstants.FULL_TEXT)):
			run_ffmpeg_command("Merge", stamp, 0)
		else:
			logger.debug("Full file exists for stamp {0}".format(stamp))
		if TCMConstants.check_file_for_read("{0}{1}-{2}".format(TCMConstants.FULL_PATH, stamp, TCMConstants.FULL_TEXT)):
			if TCMConstants.check_file_for_write("{0}{1}-{2}".format(TCMConstants.FAST_PATH, stamp, TCMConstants.FAST_TEXT)):
				run_ffmpeg_command("Fast preview", stamp, 1)
			else:
				logger.debug("Fast file exists for stamp {0}".format(stamp))
		else:
			logger.warn("Full file {0}{1}-{2} not ready for read, postponing fast preview".format(
				TCMConstants.FULL_PATH, stamp, TCMConstants.FULL_TEXT))
	else:
		logger.debug("Stamp {0} not yet ready".format(stamp))

def stamp_is_all_ready(stamp):
	front_file = "{0}{1}-{2}".format(TCMConstants.RAW_PATH, stamp, TCMConstants.FRONT_TEXT)
	left_file = "{0}{1}-{2}".format(TCMConstants.RAW_PATH, stamp, TCMConstants.LEFT_TEXT)
	right_file = "{0}{1}-{2}".format(TCMConstants.RAW_PATH, stamp, TCMConstants.RIGHT_TEXT)
	if TCMConstants.check_file_for_read(front_file) and TCMConstants.check_file_for_read(left_file) and TCMConstants.check_file_for_read(right_file) and file_sizes_in_same_range(stamp, front_file, left_file, right_file):
		return True
	else:
		return False

def file_sizes_in_same_range(stamp, front_file, left_file, right_file):
	front_size = os.path.getsize(front_file)
	left_size = os.path.getsize(left_file)
	right_size = os.path.getsize(right_file)
	if front_size == 0 or left_size == 0 or right_size == 0:
		add_to_bad_sizes(
			stamp, TCMConstants.convert_file_size(front_size),
			TCMConstants.convert_file_size(left_size),
			TCMConstants.convert_file_size(right_size))
		return False
	else:
		if abs((front_size - left_size) / front_size) > TCMConstants.SIZE_RANGE or abs((front_size - right_size) / front_size) > TCMConstants.SIZE_RANGE or abs((left_size - right_size) / left_size) > TCMConstants.SIZE_RANGE:
			add_to_bad_sizes(
				stamp, TCMConstants.convert_file_size(front_size),
				TCMConstants.convert_file_size(left_size),
				TCMConstants.convert_file_size(right_size))
			return False
		else:
			return True

### FFMPEG command functions ###

def run_ffmpeg_command(log_text, stamp, video_type):
	logger.info("{0} started: {1}...".format(log_text, stamp))
	command = get_ffmpeg_command(stamp, video_type)
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

def get_ffmpeg_command(stamp, video_type):
	if video_type == 0:
		command = "{0} -i {1}{2}-{3} -i {1}{2}-{4} -i {1}{2}-{5} {6}{7}{8} {9}{2}-{10}".format(
			ffmpeg_base, TCMConstants.RAW_PATH, stamp, TCMConstants.RIGHT_TEXT,
			TCMConstants.FRONT_TEXT, TCMConstants.LEFT_TEXT, ffmpeg_mid_full,
			format_timestamp(stamp), ffmpeg_end_full, TCMConstants.FULL_PATH, TCMConstants.FULL_TEXT)
	elif video_type == 1:
		command = "{0} -i {1}{2}-{3} {4} {5}{2}-{6}".format(
			ffmpeg_base, TCMConstants.FULL_PATH, stamp, TCMConstants.FULL_TEXT, ffmpeg_end_fast,
			TCMConstants.FAST_PATH, TCMConstants.FAST_TEXT)
	else:
		logger.error("Unrecognized video type {0} for {1}".format(video_type, stamp))
	return command

def add_to_bad_videos(name):
	simple_name = name.replace(TCMConstants.RAW_PATH, '')
	add_string_to_sorted_file(
		TCMConstants.RAW_PATH + TCMConstants.BAD_VIDEOS_FILENAME,
		simple_name, "{0}\n".format(simple_name),
		"Skipping over bad source file: {0}".format(name),
		logging.DEBUG)

def add_to_bad_sizes(stamp, front, left, right):
	add_string_to_sorted_file(
		TCMConstants.RAW_PATH + TCMConstants.BAD_SIZES_FILENAME,
		stamp,
		"{0}: Front {1}, Left {2}, Right {3}\n".format(
			stamp, front, left, right),
		"Size issue at {0}: Front {1}, Left {2}, Right {3}".format(
			stamp, front, left, right),
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
