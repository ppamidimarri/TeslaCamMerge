# TeslaCamMerge

Tesla's in-built dashcam create three separate video files, one each from the front, left and right cameras. I built this project to do the following:
1. Use the [teslausb](https://github.com/marcone/teslausb) project to have the car store videos on a Raspberry Pi Zero W and transfer the recorded videos to a network share when connected to WiFi at home
2. Merge the three videos into one 
3. Create a sped-up preview version of the merged video
4. Show the videos (raw, merged or previews) over a web browser
5. Move selected videos to my Google Drive account

## Hardware

1. Nvidia Jetson Nano (may work on Raspberry Pi with slight changes, but not tested)
2. Micro-SD card and Micro-USB power supply for the Jetson Nano
3. High-capacity SSD, e.g. Samsung T5 1TB
4. Raspberry Pi Zero W
5. Micro-USB to USB cable to plug the Pi Zero W into the car's USB port
6. Tesla car with dashcam functionality

## Instructions

**A. Setup the Jetson Nano**

1. Flash a Micro-SD card flashed with the Jetson Nano system image
2. Insert the card in the Jetson Nano
3. Connect keyboard, mouse, ethernet and monitor and power up the Nano
4. Set up a new user and password (in these instructions, you will see this ID as `<userid>`)

Once these steps are done, you can do the rest of the work on the Jetson Nano either in a terminal window in the GUI, or by setting up SSH. If you don't like `vim` as the text editor, install `nano` with `sudo apt install nano`.

**B. Install required software on the Nano**
1. `sudo apt update`
2. `sudo apt upgrade`
3. `sudo apt install exfat-fuse ffmpeg samba`

**C. Configure samba and set up the CIFS share**
1. `sudo cp /etc/samba/smb.conf{,.backup}`
2. `sudo nano /etc/samba/smb.conf`, uncomment (i.e. remove the `;` character at the beginning of) these lines:
```
	interfaces = 127.0.0.0/8 eth0
	bind interfaces only = yes
```
3. `sudo mkdir /samba`
4. `sudo chgrp sambashare /samba`
5. `sudo useradd -M -d /samba/<share-user-name> -G sambashare <share-user-name>`
6. `sudo mkdir /samba/<share-user-name>`
7. `sudo chown <share-user-name>:sambashare /samba/<share-user-name>`
8. `sudo chmod 2770 /samba/<share-user-name>`
9. `sudo smbpasswd -a <share-user-name>` and set your CIFS share password
10. `sudo smbpasswd -e <share-user-name>`

**D. Setup the locations for the dashcam footage to be stored**

1. Connect the USB SSD to the Jetson Nano
2. It should automatically be configured under `/media/<userid>`. `ls -l /media/<userid>` to check its name. Let's call the name `<drivename>`.
3. `mkdir /media/<userid>/<drivename>/Footage`
4. `mkdir /media/<userid>/<drivename>/Footage/Raw`
5. `mkdir /media/<userid>/<drivename>/Footage/Full`
6. `mkdir /media/<userid>/<drivename>/Footage/Fast`
7. `mkdir /media/<userid>/<drivename>/Footage/Upload`

**E. Install and set up filebrowser**
1. `cd ~`
2. `curl -fsSL https://filebrowser.xyz/get.sh | bash`
3. `filebrowser config init`
4. `ifconfig` and note the LAN IP address of your Jetson Nano. In your home router, given your Jetson Nano a fixed LAN IP.
5. `filebrowser config set -a <LAN-IP> -r /media/<userid>/<drivename>/Footage/`
6. `filebrowser users add admin admin`
7. `filebrowser -d /home/<userid>/filebrowser.db`
8. On your computer's web browser, go to `http://<LAN-IP>:8080/`. 
9. Login as `admin` (password is `admin` as you set up in step 6 above), change password, create new (non-admin) user

**F. Install and configure rclone**

1. `wget https://downloads.rclone.org/rclone-current-linux-arm.zip` 
2. `unzip rclone-current-linux-arm.zip` 
3. `sudo cp rclone-v????-linux-arm/rclone /usr/local/bin/`
4. `rclone config` and create a remote with the name `gdrive` of type `drive`, with access of `drive.file`
5. `rm rclone*` to remove unneded files
6. In your Google Drive account, create a folder called `TeslaCam` for the uploaded videos

**G. Install the python scripts and service files**
1. `cd ~`
2. `git clone https://github.com/ppamidimarri/TeslaCamMerge`
3. `cd TeslaCamMerge`
4. Modify the paths in the python scripts (`LoadSSD.py`, `MergeTeslaCam.py`, `UploadDrive.py`) and service files (`loadSSD.service`, `mergeTeslaCam.service`. `startFileBrowser.service`. `uploadDrive.service`) to match yours from steps C and D above
5. `sudo cp loadSSD.service /lib/systemd/system`
6. `sudo cp mergeTeslaCam.service /lib/systemd/system`
7. `sudo cp uploadDrive.service /lib/systemd/system`
8. `sudo cp startFileBrowser.service /lib/systemd/system`
9. `sudo systemctl daemon-reload`
10. `sudo systemctl enable loadSSD.service`
11. `sudo systemctl enable mergeTeslaCam.service`
12. `sudo systemctl enable uploadDrive.service`
13. `sudo systemctl enable startFileBrowser.service`
14. `sudo reboot`
15. Verify that your services are running, with `systemctl status mergeTeslaCam.service`, etc. (once for each of the four services)

**H. Configure your Pi Zero W**

Follow the [one-step setup instructions](https://github.com/marcone/teslausb/blob/main-dev/doc/OneStepSetup.md) with the pre-built image and the Jetson Nano as the share server, and the username and password for the CIFS share you have set up above. 
