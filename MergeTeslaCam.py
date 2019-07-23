#!/usr/bin/env python3

# This script users ffmpeg to generate combined videos of TeslaCam footage.
# It looks for files at "raw_path" and waits for all (front, left-repeater,
# right-repeater) are available for a single timestamp. Once all three files
# are available, it merges them into one "full" file. It then creates a
# sped-up view of the "full" file as the "fast" file.

import inotify.adapters
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
ffmpeg_base = 'ffmpeg -hide_banner -loglevel quiet'
ffmpeg_mid_full = '-filter_complex "[1:v]scale=w=1.2*iw:h=1.2*ih[top];[0:v]scale=w=0.6*iw:h=0.6*ih[right];[2:v]scale=w=0.6*iw:h=0.6*ih[left];[left][right]hstack=inputs=2[bottom];[top][bottom]vstack=inputs=2[full];[full]drawtext=text=\''
ffmpeg_end_full = '\':fontcolor=white:fontsize=48:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2" -movflags +faststart -threads 0'
ffmpeg_end_fast = '-vf "setpts=0.09*PTS" -c:v libx264 -crf 28 -profile:v main -tune fastdecode -movflags +faststart -threads 0'
watermark_timestamp_format = '%b %-d\, %-I\:%M %p'

# Lists to keep track of work to be done
fronts = []
lefts = []
rights = []

def main():
	fh = logging.FileHandler(TCMConstants.LOG_PATH + logger_name + TCMConstants.LOG_EXTENSION)
	fh.setLevel(TCMConstants.LOG_LEVEL)
	formatter = logging.Formatter(TCMConstants.LOG_FORMAT)
	fh.setFormatter(formatter)
	logger.addHandler(fh)
	logger.info("Starting up")

	signal.signal(signal.SIGINT, exit_gracefully)
	signal.signal(signal.SIGTERM, exit_gracefully)

	i = inotify.adapters.Inotify()

	try:
		i.add_watch(TCMConstants.RAW_PATH,
			inotify.constants.IN_CLOSE_WRITE)
		logger.debug("Added watch for {0}".format(TCMConstants.RAW_PATH))
	except:
		logger.error("Failed to add watch for {0}, exiting".format(TCMConstants.RAW_PATH))
		return

	for event in i.event_gen(yield_nones = False):
		(_, type_names, path, filename) = event
		watch_for_timestamp(filename)

def process_videos(stamp):
	logger.info("Processing videos for {0}...".format(stamp))
	run_ffmpeg_command("Merge", stamp, 0) # Full video merging three camera feeds
	run_ffmpeg_command("Fast preview", stamp, 1) # Fast video, i.e. sped-up version of Full
	logger.info("Created videos for {0}.".format(stamp))
	remove_from_worklist(stamp)

def remove_from_worklist(stamp):
	logger.debug("Removing {0} from work list".format(stamp))
	try:
		fronts.remove(stamp)
		lefts.remove(stamp)
		rights.remove(stamp)
	except ValueError:
		pass

def run_ffmpeg_command(log_text, stamp, video_type):
	logger.info("{0} started: {1}...".format(log_text, stamp))
	command = get_ffmpeg_command(stamp, video_type)
	logger.debug("Command: {0}".format(command))
	subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

def watch_for_timestamp(filename):
	try:
		stamp, camera = filename.rsplit("-", 1)
	except ValueError:
		logger.warn("Unrecognized filename: {0}".format(filename))
		return

	if camera == front_text:
		logger.debug("Found front for: {0}".format(stamp))
		if stamp in lefts and stamp in rights:
			process_videos(stamp)
		else:
			logger.debug("Not yet ready to merge: {0}".format(stamp))
			fronts.append(stamp)
	elif camera == left_text:
		logger.debug("Found left for: {0}".format(stamp))
		if stamp in fronts and stamp in rights:
			process_videos(stamp)
		else:
			logger.debug("Not yet ready to merge: {0}".format(stamp))
			lefts.append(stamp)
	elif camera == right_text:
		logger.debug("Found right for: {0}".format(stamp))
		if stamp in fronts and stamp in lefts:
			process_videos(stamp)
		else:
			logger.debug("Not yet ready to merge: {0}".format(stamp))
			rights.append(stamp)
	else:
		logger.warn("Unrecognized filename: {0}".format(filename))

def exit_gracefully(signum, frame):
	logger.info("Received signal number {0}, exiting.".format(signum))
	exit()

if __name__ == '__main__':
	main()
