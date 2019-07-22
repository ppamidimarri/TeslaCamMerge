# TeslaCamMerge
Merge TeslaCam files into one and serve them over the web

## Hardware

* Nvidia Jetson Nano (may work on Raspberry Pi with slight changes, but not tested)
* High-capacity SSD, e.g. Samsung T5 1TB

## Instructions
Load up Jetson Nano stuff
Connect keyboard, mouse, ethernet and monitor. Do NOT connect USB SSD
Set up a new user and set autologin
sudo apt update
sudo apt upgrade
sudo apt install nano
sudo apt install exfat-fuse
sudo apt install ffmpeg
sudo apt install samba

Change prompt: nano .bashrc, change PS1 to be color

sudo nano /root/.nanorc
nano ~/.nanorc

Setup samba:
sudo cp /etc/samba/smb.conf{,.backup}
sudo nano /etc/samba/smb.conf, uncomment:
	interfaces = 127.0.0.0/8 eth0
	bind interfaces only = yes

TM3-fJN#2

sudo mkdir /samba
sudo chgrp sambashare /samba
sudo useradd -M -d /samba/fjnuser -G sambashare fjnuser
sudo mkdir /samba/fjnuser
sudo chown fjnuser:sambashare /samba/fjnuser
sudo chmod 2770 /samba/fjnuser
sudo smbpasswd -a fjnuser
sudo smbpasswd -e fjnuser

Connect USB SSD. It should automatically be configured under /media/<userid>. 
In the SSD (e.g. /media/<userid>/Samsung_T5/), create this folder structure:
- Footage
	- Fast
	- Full
	- Raw
	- Upload

curl -fsSL https://filebrowser.xyz/get.sh | bash
filebrowser config init
filebrowser config set -a <LAN IP> -r /media/<userid>/<drivename>/Footage/
filebrowser users add admin admin
filebrowser -d /home/<userid>/filebrowser.db

On the browser, browse to http://<LAN IP>:8080/. 
Login as admin, change password, create new user
