import setproctitle #Set process name to something easily killable
from threading import Thread
import cv2
import os
import subprocess #so I can run subprocesses in the background if I want
#import ConfigParser #To read the config file modified by menu.py
from subprocess import call #to call a process in the foreground
import csv #To make an array of the certainty and identity results so we can find the top matches
from operator import itemgetter
import time


class Facedetect:
	def __init__(self, cam, cfg):
		self.cam = cam
		self.Config = cfg
		self.faceframe = "/dev/shm/face_frame" #Signal to the FacialDetectionProcess that a frame is available
		self.faceimg = "/dev/shm/face.jpg" #The frame
		self.classify = "/dev/shm/face.txt" #position of face detected if detected
		self.facetext = "/dev/shm/face_text" #FacialDetectionProcess creates this can be fetched
		self.running = False

	def start(self):

		if (os.path.exists(self.faceframe)):
			os.remove(self.faceframe)
		if (os.path.exists(self.faceimg)):
			os.remove(self.faceimg)
		if (os.path.exists(self.facetext)):
			os.remove(self.facetext)
		if (os.path.exists(self.classify)):
			os.remove(self.classify)
		print "launching face detect analysis"
		time.sleep(1)
		subprocess.Popen(["sudo","python", "/home/pi/webcam_face_detection/cam.py","--face","/home/pi/webcam_face_detection/cascades/haarcascade_frontalface_default.xml"])
		self.running = True
		t = Thread(target=self.worker, args=())
		t.start()

	def worker(self):
		while True:
			if not self.running:
				return
				

			if (not os.path.exists(self.faceframe)):
				print "face frame file not detected generating face.jpg"
				res = cv2.resize(self.cam.read(), (640, 480), interpolation =cv2.INTER_AREA)
				cv2.imwrite(self.faceimg, res)
				os.mknod(self.faceframe)
				continue

			if (os.path.exists(self.facetext)):
				print "reading report from face detect analysis"
				time.sleep(0.5)
				data = csv.reader(open('/dev/shm/face.txt', 'rb'), delimiter=",", quotechar='|')
				locX, locY, H, W, xres, yres = [], [], [], [], [], []
				for row in data:
					locX.append(row[0])
					locY.append(row[1])
					H.append(row[2])
					W.append(row[3])
					xres.append(row[4])
					yres.append(row[5])
				print "x Location",locX
				print "y Location",locY
				print "rect height", H
				print "rect width", W
				print "xres ", xres
				print "yres ",yres

				locX = [int(i) for i in locX]
				locX = locX[0]
				locY = [int(i) for i in locY]
				locY = locY[0]
				H = [int(i) for i in H]
				H = H[0]
				W = [int(i) for i in W]
				W = W[0]
				xres = [int(i) for i in xres]
				xres = xres[0]
				yres = [int(i) for i in yres]
				yres = yres[0]
				
				centeredX = locX + (W * 0.5) # Center X of box
				centeredY = locY + (H *0.5) #Center Y of box
				print "centered X",centeredX
				print "centered Y", centeredY
				bottomthirdY = 0.33*yres  #split total y resolution into thirds
				midthirdY = 0.66*yres
				topthirdY = yres				
		
				leftthirdX = 0.33*xres #split x resolution into thirds
				midthirdX = 0.66*xres
				rightthirdX = xres
				
				#Now we can classify an x and y position based on grid locations in thirds
				xstring = ""
				ystring = ""
				espeakstring = ""
				if locX == 0 and locY == 0:
					espeakstring = ""  #This is what happens when no image gets processed, or no face is detected.
					xstring = ""
					ysrting = ""
				else:
					espeakstring = "face at" #if there are other values, there is a face detected

				if centeredX > 0 and centeredX < leftthirdX:
					xstring = "left"
				elif centeredX > leftthirdX and centeredX < midthirdX:
					xstring = "Center"
				elif centeredX > midthirdX and centeredX < rightthirdX:
					xstring = "right"

				if centeredY > 0  and centeredY < bottomthirdY:  #Note due to the x,y coord system in opencv the y axis thirds are reversed compared to many other systems
					ystring = "Upper"
				elif centeredY > bottomthirdY and centeredY < midthirdY:
					ystring = "mid"
				elif centeredY > midthirdY and centeredY < topthirdY:
					ystring = "Lower"
 
				espeakstring = espeakstring + xstring + ystring # read location and size
				print "trying to read location and size"
				espeak_process = subprocess.Popen(["espeak",espeakstring, "--stdout"], stdout=subprocess.PIPE)
				aplay_process = subprocess.Popen(["aplay", "-D", "sysdefault"], stdin=espeak_process.stdout, stdout=subprocess.PIPE)
				aplay_process.wait()#wait to speak location
				call (["sudo","rm","-rf","/dev/shm/face.txt"]) #remove last run of facial detection  info
				os.remove(self.facetext)
				



	def stop(self):
		self.running = False
		call (["sudo","killall","FacialDetectProcess"]) #Kills Facial Detection Process loop
		
