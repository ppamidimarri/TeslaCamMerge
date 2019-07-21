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

logger_name = 'MergeTeslaCam'
front_text = 'front.mp4'
left_text = 'left_repeater.mp4'
right_text = 'right_repeater.mp4'
full_path = '/media/pavan/Samsung_T5/Footage/Full/'
raw_path = '/media/pavan/Samsung_T5/Footage/Raw/'
fast_path = '/media/pavan/Samsung_T5/Footage/Fast/'
full_text = 'full.mp4'
fast_text = 'fast.mp4'
ffmpeg_base = 'ffmpeg -hide_banner -loglevel quiet -i '
ffmpeg_mid_full = ' -filter_complex "[1:v]scale=w=1.2*iw:h=1.2*ih[top];[0:v]scale=w=0.6*iw:h=0.6*ih[right];[2:v]scale=w=0.6*iw:h=0.6*ih[left];[left][right]hstack=inputs=2[bottom];[top][bottom]vstack=inputs=2[full];[full]drawtext=text=\''
ffmpeg_end_full = '\':fontcolor=white:fontsize=48:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2" -movflags +faststart -threads 0 '
ffmpeg_end_fast = ' -vf "setpts=0.09*PTS" -c:v libx264 -crf 28 -profile:v main -tune fastdecode -movflags +faststart -threads 0 '
fronts = []
lefts = []
rights = []

def main():
	signal.signal(signal.SIGINT, exit_gracefully)
	signal.signal(signal.SIGTERM, exit_gracefully)

	i = inotify.adapters.Inotify()

	i.add_watch(raw_path,
		inotify.constants.IN_CLOSE_WRITE)

	logging.getLogger(logger_name).setLevel(logging.DEBUG)
	fh = logging.FileHandler('/home/pavan/log/MergeTeslaCam.log')
	fh.setLevel(logging.INFO)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	fh.setFormatter(formatter)
	logging.getLogger(logger_name).addHandler(fh)
	logging.getLogger(logger_name).info("Starting up")

	for event in i.event_gen(yield_nones = False):
		(_, type_names, path, filename) = event
		watch_for_timestamp(filename)

def process_videos(stamp):
	logging.getLogger(logger_name).info("Processing videos for {0}...".format(stamp))
	merge_videos_into_full(stamp)
	create_fast(stamp)
	logging.getLogger(logger_name).info("Created videos for {0}.".format(stamp))
	remove_from_worklist(stamp)

def remove_from_worklist(stamp):
	logging.getLogger(logger_name).debug("Removing {0} from work list".format(stamp))
	try:
		fronts.remove(stamp)
		lefts.remove(stamp)
		rights.remove(stamp)
	except ValueError:
		pass

def merge_videos_into_full(stamp):
	logging.getLogger(logger_name).info("Merging: {0}...".format(stamp))
	command = get_ffmpeg_command(stamp, 0)
	logging.getLogger(logger_name).debug("Command: {0}".format(command))
	subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	logging.getLogger(logger_name).info("Merged: {0}.".format(stamp))

def create_fast(stamp):
	logging.getLogger(logger_name).info("Creating sped-up view: {0}...".format(stamp))
	command = get_ffmpeg_command(stamp, 1)
	logging.getLogger(logger_name).debug("Command: {0}".format(command))
	subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	logging.getLogger(logger_name).info("Created sped-up view: {0}.".format(stamp))

def get_ffmpeg_command(stamp, level):
	command = ffmpeg_base
	if level == 0:
		command += raw_path + stamp + "-" + right_text + " -i " + raw_path + stamp + "-" + front_text + " -i " + raw_path + stamp + "-" + left_text + ffmpeg_mid_full + format_timestamp(stamp) + ffmpeg_end_full + full_path + stamp + "-" + full_text
	elif level == 1:
		command += full_path + stamp + "-" + full_text + ffmpeg_end_fast + fast_path + stamp + "-" + fast_text
	return command

def format_timestamp(stamp):
	timestamp = datetime.datetime.strptime(stamp, "%Y-%m-%d_%H-%M-%S")
	logging.getLogger(logger_name).debug("Timestamp: {0}".format(timestamp))
	return timestamp.strftime("%b %-d\, %-I\:%M %p")

def watch_for_timestamp(filename):
	try:
		stamp, camera = filename.rsplit("-", 1)
	except ValueError:
		logging.getLogger(logger_name).warn("Unrecognized filename: {0}".format(filename))
		return

	if camera == front_text:
		logging.getLogger(logger_name).debug("Found front for: {0}".format(stamp))
		if stamp in lefts and stamp in rights:
			process_videos(stamp)
		else:
			logging.getLogger(logger_name).debug("Not yet ready to merge: {0}".format(stamp))
			fronts.append(stamp)
	elif camera == left_text:
		logging.getLogger(logger_name).debug("Found left for: {0}".format(stamp))
		if stamp in fronts and stamp in rights:
			process_videos(stamp)
		else:
			logging.getLogger(logger_name).debug("Not yet ready to merge: {0}".format(stamp))
			lefts.append(stamp)
	elif camera == right_text:
		logging.getLogger(logger_name).debug("Found right for: {0}".format(stamp))
		if stamp in fronts and stamp in lefts:
			process_videos(stamp)
		else:
			logging.getLogger(logger_name).debug("Not yet ready to merge: {0}".format(stamp))
			rights.append(stamp)
	else:
		logging.getLogger(logger_name).warn("Unrecognized filename: {0}".format(filename))

def exit_gracefully(signum, frame):
	logging.getLogger(logger_name).info("Received signal number {0}, exiting.".format(signum))
	exit()

if __name__ == '__main__':
	main()
