#!/bin/sh
sudo rm -rf /home/pi/raspivoice
cp -a /home/pi/After-Sight-Model-1/raspivoice /home/pi/
cd /home/pi/raspivoice
make CONFIG=release_rpi2
