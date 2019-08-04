# TeslaCamMerge

Tesla's in-built dashcam create three separate video files, one each from the front, left and right cameras. I built this project to do the following:
1. Use the [teslausb](https://github.com/marcone/teslausb) project to have the car store videos on a Raspberry Pi Zero W and transfer the recorded videos to a network share when connected to WiFi at home
2. Merge the three videos into one 
3. Create a sped-up preview version of the merged video
4. Show the videos (raw, merged or previews) over a web browser
5. Move selected videos to cloud storage (e.g. Google Drive)

## How it works

The Pi Zero W is always connected to the car's USB port. In there, it acts presents itself as a USB storage device to the car. The car saves videos to the Pi Zero W's Micro-SD card when sentry events occur, or when the user presses the camera icon on the display. These clips are a minute long, and three clips are produced for each minute. 

The Jetson Nano stays at home and is always on and connected to the network. It has an SMB share that maps to the Jetson Nano's Micro-SD card. There is a high-capacity USB SSD connected to the Jetson Nano. The Jetson Nano hosts a web site that displays the contents of the USB SSD. 

The Pi Zero W connects to the home WiFi network when in range, and tries to access the SMB share on the Jetson Nano. When the share is reachable, the Pi Zero W moves over all recorded files to that share.  

When any new files are loaded on the SMB share, this application moves them from the Micro-SD card on the Jetson Nano over to the USB SSD. Once all three clips for any particular timestamp (i.e. front, left and right camera videos) are available on the USB SSD, this application then merges them into one mp4 file. It then creates a fast preview of the merged clip. 

You can easily access all the videos (raw clips from TeslaCam, merged full videos, or fast-preview versions) through a web browser. There is an "Upload" folder on the USB SSD. The web site allows you to easily copy / move files into that "Upload" folder. This application takes any files placed in that "Upload" folder and moves them to cloud storage. 

I have an nginx reverse proxy for my home that I set up for other projects. The Jetson Nano's web site for viewing video files is behind that reverse proxy, so I can access my available dashcam footage over the internet. The instructions on this project do not cover how to set up a reverse proxy. 

## [Screenshots](https://imgur.com/a/2Jl6kED)

![Login screen](https://imgur.com/cOnudbd)

## Hardware needed

1. [Nvidia Jetson Nano](https://developer.nvidia.com/buy-jetson?product=jetson_nano&location=US) (may work on Raspberry Pi with slight changes, but not tested)
2. Micro-SD card and [Micro-USB power supply](https://www.adafruit.com/product/1995) for the Jetson Nano
3. High-capacity USB SSD, e.g. [Samsung T5 1TB](https://smile.amazon.com/Samsung-T5-Portable-SSD-MU-PA1T0B/dp/B073H552FJ/)
4. [Raspberry Pi Zero W](https://smile.amazon.com/gp/product/B06XFZC3BX/)
5. Micro-USB to USB cable to plug the Pi Zero W into the car's USB port
6. Tesla car with dashcam functionality

I use a 32GB Micro-SD card on the Jetson Nano, and a 128GB card on the Pi Zero W. The amount of storage you need on the Pi depends on how long you may be away from home. 

I chose the Jetson Nano as it does the video merges with ffmpeg 4-5 times faster than a Raspberry Pi 3B+. I don't yet have a Raspberry Pi 4. The Pi 4 *may* achieve similar performance as the Jetson Nano at half the price. 

## Instructions

**A. Setup the Jetson Nano**

If you are new to the Jetson Nano, start with the [Getting Started guide from Nvidia](https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit#intro).

1. Flash a Micro-SD card with the [Jetson Nano system image](https://developer.nvidia.com/jetson-nano-sd-card-image-r322)
2. Insert the card in the Jetson Nano
3. Connect keyboard, mouse, ethernet cable and monitor and power up the Nano
4. Set up a new user and password (in these instructions, you will see this ID as `<userid>`)

Once these steps are done, you can do the rest of the work on the Jetson Nano either in a terminal window in the GUI, or by setting up SSH. 

If you don't like `vim` as the text editor, install `nano` with `sudo apt install nano` on the Jetson Nano. `nano` comes preinstalled on Raspberry Pi. If you prefer `vim`, use that instead of `nano` in the instructions below.

**B. Install required software on the Nano**
1. `sudo apt update`
2. `sudo apt upgrade`
3. `sudo apt install exfat-fuse ffmpeg samba lsof`

**C. Configure [samba](https://www.samba.org/) and set up the SMB share**
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
9. `sudo smbpasswd -a <share-user-name>` and set your SMB share password
10. `sudo smbpasswd -e <share-user-name>`
11. `sudo nano /etc/samba/smb.conf`, scroll to the bottom of the file and add:
```
# Settings for TM3 dashcam footage
[fdrive]
   path = /samba/<share-user-name>
   browseable = no
   read only = no
   force create mode = 0660
   force directory mode = 2770
   valid users = <share-user-name> @sadmin
```

**D. Setup the locations for the dashcam footage to be stored**
1. Connect the USB SSD to the Jetson Nano and wait for it to be mounted
2. It should automatically be configured under `/media/<userid>`. `ls -l /media/<userid>` to check its name. Let's call the name `<drivename>`.
3. `mkdir /media/<userid>/<drivename>/Footage`
4. `mkdir /media/<userid>/<drivename>/Footage/Raw`
5. `mkdir /media/<userid>/<drivename>/Footage/Full`
6. `mkdir /media/<userid>/<drivename>/Footage/Fast`
7. `mkdir /media/<userid>/<drivename>/Footage/Upload`

**E. Install and set up [filebrowser](https://filebrowser.xyz/)**
1. `cd ~`
2. `mkdir log` (or any other location you want your log files in)
3. `curl -fsSL https://filebrowser.xyz/get.sh | bash`
4. `ifconfig` and note the LAN IP address of your Jetson Nano. In your home router, given your Jetson Nano a fixed LAN IP.
5. `filebrowser config init -a <LAN-IP> -r /media/<userid>/<drivename>/Footage/ -l /home/<userid>/log/filebrowser.log --branding.files /home/<userid>/TeslaCamMerge --branding.disableExternal --branding.name "TM3 Footage"`
6. `filebrowser users add admin admin --perm.admin`
7. `filebrowser -d /home/<userid>/filebrowser.db`
8. On your computer's web browser, go to `http://<LAN-IP>:8080/` 
9. Login as `admin` (password is `admin` as you set up in step 6 above), change password
10. Create a new (non-admin) user account and password for routine use of the application

**F. Install and configure [rclone](https://rclone.org/)**

If you do not need the ability to upload your videos to the cloud, you can safely skip this section F. If you skip this section, you should also skip step 12 in section G below. You can also remove the "Upload" folder set up in step 7 of section D above with `rmdir /media/<userid>/<drivename>/Footage/Upload`.

1. `wget https://downloads.rclone.org/rclone-current-linux-arm.zip` 
2. `unzip rclone-current-linux-arm.zip` 
3. `sudo cp rclone-v????-linux-arm/rclone /usr/local/bin/`
4. `rclone config` and create a remote (e.g. with the name `gdrive` of type `drive`, with access of `drive.file`)
5. `rm rclone*` to remove unneded files
6. In your cloud (e.g. Google Drive) account, create a folder called `TeslaCam` for the uploaded videos

**G. Install the python scripts and service files**
1. `cd ~`
2. `git clone https://github.com/ppamidimarri/TeslaCamMerge`
3. `cd TeslaCamMerge`
4. `chmod +x *.py`
5. Modify the paths and other entries in `TCMConstants.py` to match your structure from all the previous steps
6. Once all paths are correct, run `python3 CreateServiceFiles.py`, then verify that the service files have been updated with your information (e.g. verify that `mergeTeslaCam.service` has the correct user ID, path to `MergeTeslaCam.py`, and SSD mount point)
7. `sudo cp *.service /lib/systemd/system`
8. `sudo systemctl daemon-reload`
9. `sudo systemctl enable loadSSD.service`
10. `sudo systemctl enable mergeTeslaCam.service`
11. `sudo systemctl enable startFileBrowser.service`
12. `sudo systemctl enable uploadDrive.service`
13. `sudo reboot`
14. Verify that your services are running, with `systemctl status mergeTeslaCam.service`, etc. (once for each of the four services)

Now you are done with setting up your Jetson Nano! 

**H. Configure your Pi Zero W**

Follow the [one-step setup instructions](https://github.com/marcone/teslausb/blob/main-dev/doc/OneStepSetup.md) with the pre-built image and the Jetson Nano as the share server, and the username and password for the SMB share you have set up above. 

**I. Make your footage accessible over the internet**

This is an optional step. You can access your videos using a browser on your phone or computer at home. If you want to access them over the internet, you need to set up a reverse proxy. You can set up the reverse proxy on the same Jetson Nano or Raspberry Pi you run this project on (but not the Pi Zero W). I use nginx for the reverse proxy, and here is an outline of how to get it going. Please research how to set up a secure reverse proxy before doing this.

1. `sudo apt install nginx`
2. On your main router, assign a fixed LAN IP address to the device running the website. 
2. On your main router, forward ports 80 and 443 to that fixed LAN IP address. 
4. Identify your WAN IP address. You can do this by googling "what's my IP" in a browser. Let's say it is 123.234.213.120. Try the URL http://123.234.213.120/ from your phone with the phone not on your home WiFi (turn the phone's WiFi off for this test). That way you are trying to reach your reverse proxy server from the internet, not your home network. You should see a "Welcome to nginx" page. 
5. Then edit `sudo nano /etc/nginx/sites-available/default` to add a new `location` block with a `proxy_pass` line. Details [here](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/). Example: 
``` 
location / {
	proxy_pass http://192.168.1.16:8080/;
}
``` 
7. Restart nginx.
8. Try accessing http://123.234.213.120/ on your phone with WiFi off.  
9. If the above test worked, then try it in the car browser. Bookmark the page in the car browser.

Your WAN IP address _may_ be dynamic -- that is at your ISP's discretion. If it is, saving a bookmark with the number will stop working when the ISP gives you a new WAN IP. To get around this, you need to jump through a few more hoops. 

1. Select a dynamic DNS service. I picked NoIP.com. 
2. Create a domain there. Many services let you set up a free subdomain (e.g. `myteslacam.ddns.net`).
3. On the device running this project (not the Pi Zero W in the car), install the dynamic update client provided by the dynamic DNS service you picked. This service will ping the service provider once every so often and tell them, "hey, my IP address is x.x.x.x." When the service provider sees a change in the IP address, they change their DNS records so that when you try to reach `myteslacam.ddns.net` over the internet, it will be routed to your new WAN IP. 
4. Now try your new URL in the car (e.g. http://myteslacam.ddns.net/). Bookmark it! 

If you decide to do all this, I highly recommend securing your reverse proxy server by forcing SSL on all requests and getting your own SSL certificate. There is a lot of documentation out there on how to secure an nginx server. 
