#!/bin/sh
cd /home/pi
#This script installs dependencies when required. Immediately after they install, a 'hold' is placed on them to 
#stop additional updating. IF IT'S WORKING, LEAVE IT ALONE. If you need to unhold and upgrade a package
#please do that in the updatenumber related script that performs a one-time activity. 
sudo apt-get -y install python git-core nano python-dev python-rpi.gpio python-pip espeak make gcc  python-setuptools python-numpy python-serial python-setproctitle pulseaudio python-pyaudio psmisc build-essential cmake pkg-config
sudo apt-mark hold python git-core nano python-dev python-rpi.gpio python-pip espeak make gcc  python-setuptools python-numpy python-serial python-setproctitle pulseaudio python pyaudio psmisc build-essential cmake pkg-config
#Sometimes things that can't be installed by apt-get can be installed by pip ONLY. for things that 
#apt-get cant handle, we place them here, but we PREFER to use apt-get
sudo pip install wiringpi2
