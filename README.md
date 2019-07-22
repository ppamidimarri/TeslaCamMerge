# TeslaCamMerge
Merge TeslaCam files into one and serve them over the web

## Hardware

* Nvidia Jetson Nano (may work on Raspberry Pi with slight changes, but not tested)
* Micro-SD card and Micro-USB power supply for the Jetson Nano
* High-capacity SSD, e.g. Samsung T5 1TB

## Instructions
Flash a Micro-SD card flashed with the Jetson Nano system image. Insert the card in the Jetson Nano. 
Connect keyboard, mouse, ethernet and monitor. Do NOT connect USB SSD yet. Power up the Jetson Nano.
Set up a new user and set autologin
`sudo apt update`
`sudo apt upgrade`
`sudo apt install nano exfat-fuse ffmpeg samba`

Setup samba:
`sudo cp /etc/samba/smb.conf{,.backup}`
`sudo nano /etc/samba/smb.conf`, uncomment:
	`interfaces = 127.0.0.0/8 eth0`
	`bind interfaces only = yes`

`sudo mkdir /samba`
`sudo chgrp sambashare /samba`
`sudo useradd -M -d /samba/fjnuser -G sambashare fjnuser`
`sudo mkdir /samba/fjnuser`
`sudo chown fjnuser:sambashare /samba/fjnuser`
`sudo chmod 2770 /samba/fjnuser`
`sudo smbpasswd -a fjnuser` and set your CIFS share password
`sudo smbpasswd -e fjnuser`

Connect USB SSD. It should automatically be configured under /media/<userid>. 
In the SSD (e.g. /media/<userid>/Samsung_T5/), create this folder structure:
- Footage
	- Fast
	- Full
	- Raw
	- Upload

`curl -fsSL https://filebrowser.xyz/get.sh | bash`
`filebrowser config init`
`filebrowser config set -a <LAN IP> -r /media/<userid>/<drivename>/Footage/`
`filebrowser users add admin admin`
`filebrowser -d /home/<userid>/filebrowser.db`

On the browser, browse to http://<LAN IP>:8080/. 
Login as admin, change password, create new user
