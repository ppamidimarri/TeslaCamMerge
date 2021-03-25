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
import json

# ffmpeg commands and filters
ffmpeg_base = f'{TCMConstants.FFMPEG_PATH} -hide_banner -loglevel error -timelimit {TCMConstants.FFMPEG_TIMELIMIT}'
ffmpeg_mid_full = f'-filter_complex "[1:v]scale=w={TCMConstants.FRONT_WIDTH}:h={TCMConstants.FRONT_HEIGHT}[top];[0:v]scale=w={TCMConstants.REST_WIDTH}:h={TCMConstants.REST_HEIGHT}[right];[3:v]scale=w={TCMConstants.REST_WIDTH}:h={TCMConstants.REST_HEIGHT}[back];[2:v]scale=w={TCMConstants.REST_WIDTH}:h={TCMConstants.REST_HEIGHT}[left];[left][back][right]hstack=inputs=3[bottom];[top][bottom]vstack=inputs=2[full];[full]drawtext=text=\''
ffmpeg_mid2_full = '\':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2[labeled];[labeled]drawtext=text=\''
ffmpeg_end_full = '\':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2:y=h-text_h" -movflags +faststart -threads 0'
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
		if TCMConstants.MULTI_CAR:
			for car in TCMConstants.CAR_LIST:
				loop_car(f"{car}/")
		else:
			loop_car("")

		time.sleep(TCMConstants.SLEEP_DURATION)

### Startup functions ###

def have_required_permissions():
	have_perms = True
	if TCMConstants.MULTI_CAR:
		for car in TCMConstants.CAR_LIST:
			have_perms = have_perms and check_permissions_for_car(f"{car}/")
	else:
		have_perms = have_perms and check_permissions_for_car("")
	return have_perms

def check_permissions_for_car(car_path):
	have_perms = True
	for folder in TCMConstants.FOOTAGE_FOLDERS:
		have_perms = have_perms and TCMConstants.check_permissions(f"{TCMConstants.FOOTAGE_PATH}{car_path}{folder}/{TCMConstants.RAW_FOLDER}", False)
		have_perms = have_perms and TCMConstants.check_permissions(f"{TCMConstants.FOOTAGE_PATH}{car_path}{folder}/{TCMConstants.FULL_FOLDER}", True)
		have_perms = have_perms and TCMConstants.check_permissions(f"{TCMConstants.FOOTAGE_PATH}{car_path}{folder}/{TCMConstants.FAST_FOLDER}", True)
	return have_perms

### Loop functions ###

def loop_car(car_path):
	for folder in TCMConstants.FOOTAGE_FOLDERS:
		raw_files = os.listdir(f"{TCMConstants.FOOTAGE_PATH}{car_path}{folder}/{TCMConstants.RAW_FOLDER}")
		for file in raw_files:
			logger.debug(f"Starting with file {file}")
			try:
				stamp, camera = file.rsplit("-", 1)
			except ValueError:
				if TCMConstants.EVENT_JSON not in file and file != TCMConstants.BAD_VIDEOS_FILENAME and file != TCMConstants.BAD_SIZES_FILENAME:
					logger.warn(f"Unrecognized filename: {file}")
				continue
			process_stamp(stamp, f"{car_path}{folder}")

def process_stamp(stamp, folder):
	logger.debug(f"Processing stamp {stamp} in {folder}")
	if stamp_is_all_ready(stamp, folder):
		logger.debug(f"Stamp {stamp} in {folder} is ready to go")
		if TCMConstants.check_file_for_write(f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.FULL_FOLDER}/{stamp}-{TCMConstants.FULL_TEXT}"):
			run_ffmpeg_command("Merge", folder, stamp, 0)
		else:
			logger.debug(f"Full file exists for stamp {stamp}")
		if TCMConstants.check_file_for_read(f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.FULL_FOLDER}/{stamp}-{TCMConstants.FULL_TEXT}"):
			if TCMConstants.check_file_for_write(f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.FAST_FOLDER}/{stamp}-{TCMConstants.FAST_TEXT}"):
				run_ffmpeg_command("Fast preview", folder, stamp, 1)
			else:
				logger.debug(f"Fast file exists for stamp {stamp} at {folder}")
		else:
			logger.warn(f"Full file {TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.FULL_FOLDER}/{stamp}-{TCMConstants.FULL_TEXT} not ready for read, postponing fast preview")
	else:
		logger.debug(f"Stamp {stamp} not yet ready in {folder}")

def stamp_is_all_ready(stamp, folder):
	front_file = f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.RAW_FOLDER}/{stamp}-{TCMConstants.FRONT_TEXT}"
	left_file = f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.RAW_FOLDER}/{stamp}-{TCMConstants.LEFT_TEXT}"
	right_file = f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.RAW_FOLDER}/{stamp}-{TCMConstants.RIGHT_TEXT}"
	back_file = f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.RAW_FOLDER}/{stamp}-{TCMConstants.BACK_TEXT}"
	if file_is_bad(stamp, folder):
		return False
	if TCMConstants.check_file_for_read(front_file) and TCMConstants.check_file_for_read(left_file) and TCMConstants.check_file_for_read(right_file) and TCMConstants.check_file_for_read(back_file) and file_sizes_in_same_range(folder, stamp, front_file, left_file, right_file, back_file):
		return True
	else:
		return False

def file_is_bad(stamp, folder):
	if TCMConstants.check_file_for_read(f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.RAW_FOLDER}/{TCMConstants.BAD_VIDEOS_FILENAME}"):
		with open(f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.RAW_FOLDER}/{TCMConstants.BAD_VIDEOS_FILENAME}", "r") as f:
			bad_names = f.readlines()
			check_list = [TCMConstants.FRONT_TEXT, TCMConstants.LEFT_TEXT, TCMConstants.RIGHT_TEXT, TCMConstants.BACK_TEXT]
			for item in check_list:
				if f"{stamp}-{item}\n" in bad_names:
					logger.debug(f"Skipping {stamp} in {folder} due to bad data in {stamp}-{item}")
					return True
			return False
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
	logger.info(f"{log_text} started in {stamp}: {folder}...")
	command = get_ffmpeg_command(folder, stamp, video_type)
	logger.debug(f"Command: {command}")
	completed = subprocess.run(command, shell=True,
		stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
		stderr=subprocess.PIPE)
	if completed.stderr or completed.returncode != 0:
		logger.error(f"Error running ffmpeg command: {command}, returncode: {completed.returncode}, stdout: {completed.stdout}, stderr: {completed.stderr}")
		for line in completed.stderr.decode("UTF-8").splitlines():
			match = ffmpeg_error_pattern.match(line)
			if match:
				file = match.group(1)
				if video_type == 1:
					logger.debug(f"Will try to remove bad merged file: {file}")
					try:
						os.remove(file)
					except:
						logger.warn(f"Failed to remove bad file: {file}")
				else:
					add_to_bad_videos(folder, file)
	else:
		logger.debug(f"FFMPEG stdout: {completed.stdout}, stderr: {completed.stderr}")
	logger.info(f"{log_text} completed: {stamp}.")

def get_ffmpeg_command(folder, stamp, video_type):
	logger.debug(f"Get command: folder {folder}, stamp {stamp}, type {video_type}")
	if video_type == 0:
		command = "{0} -i {1}{2}/{3}/{4}-{5} -i {1}{2}/{3}/{4}-{6} -i {1}{2}/{3}/{4}-{7} -i {1}{2}/{3}/{4}-{8} {9}{10}{11}{12}{13} {1}{2}/{14}/{4}-{15}".format(
			ffmpeg_base, TCMConstants.FOOTAGE_PATH, folder, TCMConstants.RAW_FOLDER, stamp, TCMConstants.RIGHT_TEXT,
			TCMConstants.FRONT_TEXT, TCMConstants.LEFT_TEXT, TCMConstants.BACK_TEXT, ffmpeg_mid_full,
			format_timestamp(stamp), ffmpeg_mid2_full, get_event_string(folder, stamp), ffmpeg_end_full, TCMConstants.FULL_FOLDER, TCMConstants.FULL_TEXT)
	elif video_type == 1:
		command = "{0} -i {1}{2}/{3}/{4}-{5} {6} {1}{2}/{7}/{4}-{8}".format(
			ffmpeg_base, TCMConstants.FOOTAGE_PATH, folder, TCMConstants.FULL_FOLDER, stamp, TCMConstants.FULL_TEXT, ffmpeg_end_fast,
			TCMConstants.FAST_FOLDER, TCMConstants.FAST_TEXT)
	else:
		logger.error(f"Unrecognized video type {video_type} for {stamp} in {folder}")
	logger.debug(command)
	return command

def get_event_string(folder, stamp):
	logger.debug(f"Getting event string: folder {folder}, stamp {stamp}")
	list = os.listdir(f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.RAW_FOLDER}/")
	for file in list:
		if TCMConstants.EVENT_JSON in file:
			if event_matches_stamp(file, stamp):
				with open(f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.RAW_FOLDER}/{file}", "r") as jsonfile:
					event = json.load(jsonfile)
					jsonstamp = format_timestamp(event['timestamp'].replace('T', '_').replace(':', '-'), True)
					try:
						reason = TCMConstants.EVENT_REASON[event['reason']]
					except:
						reason = event['reason']
					try:
						camera = TCMConstants.EVENT_CAMERA[event['camera']]
					except:
						camera = 'camera ' + event['camera']
					logger.debug(f"{reason} in {event['city']} at {jsonstamp} on camera {camera}")
					return f"{reason} in {event['city']} at {jsonstamp} on {camera}"
	return "No event information available"

def event_matches_stamp(file, stamp):
	file_time = datetime.datetime.fromisoformat(file.rsplit('-',1)[0].split('_')[0] + 'T' + file.rsplit('-',1)[0].split('_')[1].replace('-',':'))
	stamp_time = datetime.datetime.fromisoformat(stamp.split('_')[0] + 'T' + stamp.split('_')[1].replace('-',':'))
	max_delta = datetime.timedelta(days=0, seconds=TCMConstants.EVENT_DURATION)
	if (abs(file_time - stamp_time) <= max_delta):
		return True
	else:
		return False

def add_to_bad_videos(folder, name):
	simple_name = name.replace(f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.RAW_FOLDER}/", '')
	add_string_to_sorted_file(
		f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.RAW_FOLDER}/{TCMConstants.BAD_VIDEOS_FILENAME}",
		simple_name, f"{simple_name}\n",
		f"Skipping over bad source file: {name}",
		logging.DEBUG)

def add_to_bad_sizes(folder, stamp, front, left, right, back):
	add_string_to_sorted_file(
		f"{TCMConstants.FOOTAGE_PATH}{folder}/{TCMConstants.RAW_FOLDER}/{TCMConstants.BAD_SIZES_FILENAME}",
		stamp,
		f"{stamp}: Front {front}, Left {left}, Right {right}, Back: {back}\n",
		f"Size issue at {stamp} in {folder}: Front {front}, Left {left}, Right {right}, Back: {back}",
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

def format_timestamp(stamp, seconds=False):
	timestamp = datetime.datetime.strptime(stamp, TCMConstants.FILENAME_TIMESTAMP_FORMAT)
	logger.debug(f"Timestamp: {timestamp}")
	if seconds:
		return timestamp.strftime(TCMConstants.EVENT_TIMESTAMP_FORMAT)
	else:
		return timestamp.strftime(TCMConstants.WATERMARK_TIMESTAMP_FORMAT)

if __name__ == '__main__':
	main()
