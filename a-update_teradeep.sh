#!/bin/sh
rm -rf /home/pi/thnets
rm -rf /home/pi/teradeep_opencv
cp -a /home/pi/After-Sight-Model-1/thnets /home/pi/
cp -a /home/pi/After-Sight-Model-1/teradeep_opencv /home/pi/
cd /home/pi/thnets/OpenBLAS-stripped
make
sudo cp *.so /usr/local/lib/
sudo cp *.so /usr/lib/
cd ..
make
sudo cp thnets.so /usr/local/lib/libthnets.so
sudo cp thnets.so /usr/lib/libthnets.so
cd /home/pi/teradeep_opencv
make
