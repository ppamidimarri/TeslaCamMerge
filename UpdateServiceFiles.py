import os
import TCMConstants

def main():
  process_service_file('loadSSD.service')
  process_service_file('mergeTeslaCam.service')
  process_service_file('uploadDrive.service')
  process_service_file('startFileBrowser.service')

def process_service_file(name):
  with open(name, "rt") as fin:
    with open(name + ".tmp", "wt") as fout:
       for line in fin:
           fout.write(line.replace('PROJECT_PATH', PROJECT_PATH).replace('FILEBROWSER_PATH', FILEBROWSER_PATH))
  os.rename(name + ".tmp", name)
  
