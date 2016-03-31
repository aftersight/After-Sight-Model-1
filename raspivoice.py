import setproctitle #Set process name to something easily killable
from threading import Thread
import cv2
import os
import subprocess #so I can run subprocesses in the background if I want
#import ConfigParser #To read the config file modified by menu.py
from subprocess import call #to call a process in the foreground
import time

class Raspivoice:
        def __init__(self, cam, cfg):
                self.cam = cam #Camera object from WebcamVideoStream class
                self.Config = cfg
                self.raspiframe = "/dev/shm/raspi_frame" #Raspivoice takes this as a signal that a frame is available
                self.raspiimg = "/dev/shm/opencv.jpg" # The image
                self.raspiplayed = "/dev/shm/raspi_played" #Raspivoice creates this after playback of a frame finishes
                self.running = False

        def start(self):
                if (os.path.exists(self.raspiplayed)):
                        os.remove(self.raspiplayed)

                cmdList = ["sudo","/home/pi/raspivoice/Release/./raspivoice",self.Config.ConfigRaspivoiceCamera,self.Config.ConfigRaspivoicePlaybackSpeed,self.Config.ConfigBlinders,self.Config.ConfigZoom, self.Config.ConfigRaspivoiceContrast]
                if self.Config.ConfigFovealmapping == "--foveal_mapping":
                	cmdList.append("--foveal_mapping")
                
                subprocess.Popen(cmdList) #Launch using config settings plus a few obligate command line flags for spoken menu and rotary encoder input
                if (os.path.exists(self.raspiframe)):
                        os.remove(self.raspiframe)
                if (os.path.exists(self.raspiimg)):
                        os.remove(self.raspiimg)
                self.running = True
                t = Thread(target=self.worker, args=())
                t.start()

        def worker(self):
                while True:
                        if not self.running:
                                return

                        if (not os.path.exists(self.raspiframe)):
# We need to change the resolution if Foveal mapping is enabled
                                if self.Config.ConfigFovealmapping == "--foveal_mapping":
                                	res = cv2.resize(self.cam.read(), (320, 240), interpolation =cv2.INTER_AREA)
                                else:
                                	res = cv2.resize(self.cam.read(), (176, 64), interpolation =cv2.INTER_AREA)
                                cv2.imwrite(self.raspiimg, res)
                                os.mknod(self.raspiframe)

        def stop(self):
                self.running = False
                call (["sudo","killall","raspivoice"]) # Kills raspivoice if its running

        def restart(self):
                if not self.running:
                        return
                self.stop()
                time.sleep(1)
                self.start()
