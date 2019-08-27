#!/usr/bin/env python3

# This script geenrates prepares the correct service files for use by systemd
# based on your configuration settings in TCMConstants.py

import os
import re
import TCMConstants

replacements = {
	"FILEBROWSER_PATH" : TCMConstants.FILEBROWSER_PATH,
	"SSD_MOUNT_POINT" : TCMConstants.SSD_MOUNT_POINT,
	"PROJECT_PATH" : TCMConstants.PROJECT_PATH,
	"PROJECT_USER" : TCMConstants.PROJECT_USER
}

def main():
	process_service_file('loadSSD.service')
	process_service_file('mergeTeslaCam.service')
	process_service_file('uploadDrive.service')
	process_service_file('startFileBrowser.service')
	process_service_file('removeOld.service')
	process_service_file('downloadTC.service')

def process_service_file(name):
	if os.path.isfile(name):
		with open(name, "rt") as fin:
			with open(name + ".tmp", "wt") as fout:
				for line in fin:
					fout.write(do_replacements(line))
		os.rename(name + ".tmp", name)

def do_replacements(line):
	substrs = sorted(replacements, key=len, reverse=True)
	regexp = re.compile('|'.join(map(re.escape, substrs)))
	return regexp.sub(lambda match: replacements[match.group(0)], line)

if __name__ == '__main__':
	main()
