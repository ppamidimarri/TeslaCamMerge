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

# Characteristics of filenames output by TeslaCam
front_text = 'front.mp4'
left_text = 'left_repeater.mp4'
right_text = 'right_repeater.mp4'
full_text = 'full.mp4'
fast_text = 'fast.mp4'
filename_timestamp_format = '%Y-%m-%d_%H-%M-%S'

# ffmpeg commands and filters
ffmpeg_base = "{0} -hide_banner -loglevel quiet".format(TCMConstants.FFMPEG_PATH)
ffmpeg_mid_full = '-filter_complex "[1:v]scale=w=1.2*iw:h=1.2*ih[top];[0:v]scale=w=0.6*iw:h=0.6*ih[right];[2:v]scale=w=0.6*iw:h=0.6*ih[left];[left][right]hstack=inputs=2[bottom];[top][bottom]vstack=inputs=2[full];[full]drawtext=text=\''
ffmpeg_end_full = '\':fontcolor=white:fontsize=48:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2" -movflags +faststart -threads 0'
ffmpeg_end_fast = '-vf "setpts=0.09*PTS" -c:v libx264 -crf 28 -profile:v main -tune fastdecode -movflags +faststart -threads 0'
watermark_timestamp_format = '%b %-d\, %-I\:%M %p'

def main():
	fh = logging.FileHandler(TCMConstants.LOG_PATH + logger_name + TCMConstants.LOG_EXTENSION)
	fh.setLevel(TCMConstants.LOG_LEVEL)
	formatter = logging.Formatter(TCMConstants.LOG_FORMAT)
	fh.setFormatter(formatter)
	logger.addHandler(fh)
	logger.info("Starting up")

	signal.signal(signal.SIGINT, exit_gracefully)
	signal.signal(signal.SIGTERM, exit_gracefully)

	while True:
		stamps = []
		raw_files = os.listdir(TCMConstants.RAW_PATH)
		full_files = os.listdir(TCMConstants.FULL_PATH)
		fast_files = os.listdir(TCMConstants.FAST_PATH)

		for file in raw_files:
			try:
				stamp, camera = file.rsplit("-", 1)
			except ValueError:
				logger.warn("Unrecognized filename: {0}".format(file))
				continue
			process_stamp(stamp, raw_files, full_files, fast_files)

		time.sleep(60)

def process_stamp(stamp, raw_files, full_files, fast_files):
	logger.debug("Processing stamp {0}".format(stamp))
	if stamp_is_all_ready(stamp, raw_files):
		logger.debug("Stamp {0} is ready to go".format(stamp))
		if stamp_in_full(stamp, full_files):
			logger.debug("Full file exists for stamp {0}".format(stamp))
			if stamp_in_fast(stamp, fast_files):
				logger.debug("Fast file exists for stamp {0}".format(stamp))
			else:
				run_ffmpeg_command("Fast preview", stamp, 1)
		else:
			run_ffmpeg_command("Merge", stamp, 0)
			if stamp_in_fast(stamp, fast_files):
				logger.debug("Fast file exists for stamp {0}".format(stamp))
			else:
				run_ffmpeg_command("Fast preview", stamp, 1)
	else:
		logger.debug("Stamp {0} not yet ready".format(stamp))

def stamp_is_all_ready(stamp, raw_files):
	front_file = "{0}-{1}".format(stamp, front_text)
	left_file = "{0}-{1}".format(stamp, left_text)
	right_file = "{0}-{1}".format(stamp, right_text)
	if front_file in raw_files and left_file in raw_files and right_file in raw_files:
		return True
	else:
		return False

def stamp_in_full(stamp, full_files):
	full_file = "{0}-{1}".format(stamp, full_text)
	if full_file in full_files:
		return True
	else:
		return False

def stamp_in_fast(stamp, fast_files):
	fast_file = "{0}-{1}".format(stamp, fast_text)
	if fast_file in fast_files:
		return True
	else:
		return False

def run_ffmpeg_command(log_text, stamp, video_type):
	logger.info("{0} started: {1}...".format(log_text, stamp))
	command = get_ffmpeg_command(stamp, video_type)
	logger.debug("Command: {0}".format(command))
	subprocess.run(command, shell=True, stdin=subprocess.DEVNULL, timeout=600)
	logger.info("{0} completed: {1}.".format(log_text, stamp))

def get_ffmpeg_command(stamp, video_type):
	if video_type == 0:
		command = "{0} -i {1}{2}-{3} -i {1}{2}-{4} -i {1}{2}-{5} {6}{7}{8} {9}{2}-{10}".format(
			ffmpeg_base, TCMConstants.RAW_PATH, stamp, right_text, front_text, left_text,
			ffmpeg_mid_full, format_timestamp(stamp), ffmpeg_end_full,
			TCMConstants.FULL_PATH, full_text)
	elif video_type == 1:
		command = "{0} -i {1}{2}-{3} {4} {5}{2}-{6}".format(
			ffmpeg_base, TCMConstants.FULL_PATH, stamp, full_text, ffmpeg_end_fast,
			TCMConstants.FAST_PATH, fast_text)
	else:
		logger.error("Unrecognized video type {0} for {1}".format(video_type, stamp))
	return command

def format_timestamp(stamp):
	timestamp = datetime.datetime.strptime(stamp, filename_timestamp_format)
	logger.debug("Timestamp: {0}".format(timestamp))
	return timestamp.strftime(watermark_timestamp_format)

def exit_gracefully(signum, frame):
	logger.info("Received signal number {0}, exiting.".format(signum))
	exit(signum)

if __name__ == '__main__':
	main()
