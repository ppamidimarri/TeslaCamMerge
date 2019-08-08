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
import signal
import logging
import TCMConstants

logger_name = 'MergeTeslaCam'
logger = logging.getLogger(logger_name)
logger.setLevel(TCMConstants.LOG_LEVEL)

# ffmpeg commands and filters
ffmpeg_base = "{0} -hide_banner -loglevel quiet".format(TCMConstants.FFMPEG_PATH)
ffmpeg_mid_full = '-filter_complex "[1:v]scale=w=1.2*iw:h=1.2*ih[top];[0:v]scale=w=0.6*iw:h=0.6*ih[right];[2:v]scale=w=0.6*iw:h=0.6*ih[left];[left][right]hstack=inputs=2[bottom];[top][bottom]vstack=inputs=2[full];[full]drawtext=text=\''
ffmpeg_end_full = '\':fontcolor=white:fontsize=48:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2" -movflags +faststart -threads 0'
ffmpeg_end_fast = '-vf "setpts=0.09*PTS" -c:v libx264 -crf 28 -profile:v main -tune fastdecode -movflags +faststart -threads 0'

def main():
	fh = logging.FileHandler(TCMConstants.LOG_PATH + logger_name + TCMConstants.LOG_EXTENSION)
	fh.setLevel(TCMConstants.LOG_LEVEL)
	formatter = logging.Formatter(TCMConstants.LOG_FORMAT)
	fh.setFormatter(formatter)
	logger.addHandler(fh)
	logger.info("Starting up")

	signal.signal(signal.SIGINT, exit_gracefully)
	signal.signal(signal.SIGTERM, exit_gracefully)

	if not have_required_permissions():
		logger.error("Missing some required permissions, exiting")
		exit_gracefully(TCMConstants.SPECIAL_EXIT_CODE, None)

	while True:
		raw_files = os.listdir(TCMConstants.RAW_PATH)
		for file in raw_files:
			logger.debug("Starting with file {0}".format(file))
			try:
				stamp, camera = file.rsplit("-", 1)
			except ValueError:
				logger.warn("Unrecognized filename: {0}".format(file))
				continue
			process_stamp(stamp)

		time.sleep(TCMConstants.SLEEP_DURATION)

### Startup functions ###

def have_required_permissions():
	return TCMConstants.check_permissions(
		TCMConstants.RAW_PATH, False, logger) and TCMConstants.check_permissions(
		TCMConstants.FULL_PATH, True, logger) and TCMConstants.check_permissions(
		TCMConstants.FAST_PATH, True, logger)

def exit_gracefully(signum, frame):
	logger.info("Received signal number {0}, exiting.".format(signum))
	exit(signum)

### Loop functions ###

def process_stamp(stamp):
	logger.debug("Processing stamp {0}".format(stamp))
	if stamp_is_all_ready(stamp):
		logger.debug("Stamp {0} is ready to go".format(stamp))
		if TCMConstants.check_file_for_write("{0}{1}-{2}".format(TCMConstants.FULL_PATH, stamp, TCMConstants.FULL_TEXT), logger):
			run_ffmpeg_command("Merge", stamp, 0)
		else:
			logger.debug("Full file exists for stamp {0}".format(stamp))
		if TCMConstants.check_file_for_read("{0}{1}-{2}".format(TCMConstants.FULL_PATH, stamp, TCMConstants.FULL_TEXT), logger):
			if TCMConstants.check_file_for_write("{0}{1}-{2}".format(TCMConstants.FAST_PATH, stamp, TCMConstants.FAST_TEXT), logger):
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
	if TCMConstants.check_file_for_read(front_file, logger) and TCMConstants.check_file_for_read(left_file, logger) and TCMConstants.check_file_for_read(right_file, logger):
		return True
	else:
		return False

### FFMPEG command functions ###

def run_ffmpeg_command(log_text, stamp, video_type):
	logger.info("{0} started: {1}...".format(log_text, stamp))
	command = get_ffmpeg_command(stamp, video_type)
	logger.debug("Command: {0}".format(command))
	subprocess.run(command, shell=True, stdin=subprocess.DEVNULL)
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

### Other utility functions ###

def format_timestamp(stamp):
	timestamp = datetime.datetime.strptime(stamp, TCMConstants.FILENAME_TIMESTAMP_FORMAT)
	logger.debug("Timestamp: {0}".format(timestamp))
	return timestamp.strftime(TCMConstants.WATERMARK_TIMESTAMP_FORMAT)

if __name__ == '__main__':
	main()
