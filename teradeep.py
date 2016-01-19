import setproctitle #Set process name to something easily killable
from threading import Thread
import cv2
import os
import subprocess #so I can run subprocesses in the background if I want
#import ConfigParser #To read the config file modified by menu.py
from subprocess import call #to call a process in the foreground
import csv #To make an array of the certainty and identity results so we can find the top matches
from operator import itemgetter

class Teradeep:
	def __init__(self, cam, cfg):
		self.cam = cam
		self.Config = cfg
		self.teraframe = "/dev/shm/tera_frame" #Signal to the teradeep process that a frame is available
		self.teraimg = "/dev/shm/teradeep.jpg" #The frame
		self.classify = "/dev/shm/teradeep.txt"
		self.teratext = "/dev/shm/tera_text" #Teradeep process creates this when text in classify can be fetched
		self.running = False

	def start(self):
#		self.Config.read('/home/pi/aftersight.cfg')
#		self.ConfigJetpacThreshold = float(self.Config.get('AfterSightConfigSettings','configjetpacthreshold')) #Set the identification threshold as a float

		if (os.path.exists(self.teraframe)):
			os.remove(self.teraframe)
		if (os.path.exists(self.teraimg)):
			os.remove(self.teraimg)
		if (os.path.exists(self.teratext)):
			os.remove(self.teratext)
		if (os.path.exists(self.classify)):
			os.remove(self.classify)

		subprocess.Popen(["sudo","/home/pi/teradeep_opencv/teradeep_opencv","-m","/home/pi/teradeep_model/","-i","/dev/shm/teradeep.jpg"])
		self.running = True
		t = Thread(target=self.worker, args=())
		t.start()

	def worker(self):
		while True:
			if not self.running:
				return
				

			if (not os.path.exists(self.teraframe)):
				res = cv2.resize(self.cam.read(), (640, 480), interpolation =cv2.INTER_AREA)
				cv2.imwrite(self.teraimg, res)
				os.mknod(self.teraframe)
				continue

			if (os.path.exists(self.teratext)):
				data = csv.reader(open('/dev/shm/teradeep.txt', 'rb'), delimiter="	", quotechar='|')
				certainty, identity = [], []
				
				for row in data:
				   certainty.append(row[0])
				   identity.append(row[1])
				
				
				certainty = [float(i) for i in certainty] # Convert Certainty from string to float to allow sorting
				matrix = zip(certainty, identity) #combine them into a two dimentional list
				matrix.sort(key=itemgetter(0), reverse=True) #Sort Highest to Lowest Based on Certainty
				#Now Espeak the top three terms if they are > threshold
				topthreeidentity = [x[1] for x in matrix[0:3]]
				topthreecertainty = [x[0] for x in matrix[0:3]]
				if topthreecertainty[0] > float(self.Config.ConfigTeradeepThreshold):
					FirstItem = str(topthreeidentity[0])
					print topthreecertainty[0], topthreeidentity[0]," 1st item Greater Than Threshold"
				else:
					FirstItem = "Nothing Recognized"
					print "Top item underthreshold"
				
				if topthreecertainty[1] > float(self.Config.ConfigTeradeepThreshold):
					SecondItem = str(topthreeidentity[1])
					print topthreecertainty[1], topthreeidentity[1], " 2nd item Greater Than Threshold"
				else:
					SecondItem =  " "
					print "Second Item Under Threshold"
				
				if topthreecertainty[2] > float(self.Config.ConfigTeradeepThreshold):
					ThirdItem = str(topthreeidentity[2])
					print topthreecertainty[2], topthreeidentity[2], " 3rd item Greater Than Threshold"
				else:
					ThirdItem = " "
				
				espeakstring = FirstItem + ", " + SecondItem + ", " + ThirdItem # read top three, commas to make a small pause

#				topthree = [x[1] for x in matrix[0:3]]
#				espeakstring = str(topthree[0]) + ", " + str(topthree[1]) + ", " + str(topthree[2])
				espeak_process = subprocess.Popen(["espeak",espeakstring, "--stdout"], stdout=subprocess.PIPE)
				subprocess.Popen(["aplay", "-D", "sysdefault"], stdin=espeak_process.stdout, stdout=subprocess.PIPE)
				call (["sudo","rm","-rf","/dev/shm/teradeep.txt"]) #remove last run of classification info
				os.remove(self.teratext)




	def stop(self):
		self.running = False
		call (["sudo","killall","teradeep_opencv"]) #Kills Teradeep C++ loop
		
