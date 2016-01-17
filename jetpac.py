import setproctitle #Set process name to something easily killable
import cv2 #Computer Vision Libraries for webcam use
import subprocess #so I can run subprocesses in the background if I want
import ConfigParser #To read the config file modified by menu.py
from subprocess import call #to call a process in the foreground
import csv #To make an array of the certainty and identity results so we can find the top matches
from operator import itemgetter
from imutils.video import WebcamVideoStream
setproctitle.setproctitle("jetpac")
Config = ConfigParser.RawConfigParser()
Config.read('/home/pi/aftersight.cfg')

ConfigJetpacNetwork = Config.get('AfterSightConfigSettings','configjetpacnetwork') #Get the path to the selected network from the config
ConfigJetpacThreshold = Config.get('AfterSightConfigSettings','configjetpacthreshold') #Set the identification threshold
ConfigJetpacCamera = Config.get('AfterSightConfigSettings','configjetpaccamera') #Get Selected Camera - Not implemented yet
ConfigJetpacThreshold = float(ConfigJetpacThreshold)#Convert to float so I can compare to other numbers

print ConfigJetpacNetwork
print ConfigJetpacThreshold
print ConfigJetpacCamera

camera_port = 0 #Open Camera 0
camera = WebcamVideoStream(src=camera_port).start() #define where I dump camera input


classify = "/dev/shm/classify.txt"


while 1:
   image = camera.read()
   cv2.imwrite("/dev/shm/opencv.png", image)

   #./jpcnn -i data/dog.jpg -n ../networks/jetpac.ntwk -t -m s -d
   #Command Line for jetpac I dropped -t and -d because when it works I dont need to know how long it takes or the debug info
   with open (classify, "w+") as f: #write results to classify.txt
      call (["sudo","/home/pi/projects/DeepBeliefSDK/source/./jpcnn","-i","/dev/shm/opencv.png","-n",ConfigJetpacNetwork,"-m","s"],stdout = f,stderr = f)
   call (["sudo","rm","-rf","/dev/shm/opencv.png"])
   data = csv.reader(open('/dev/shm/classify.txt', 'rb'), delimiter="   ", quotechar='|')
   certainty, identity = [], []

   for row in data:
      certainty.append(row[0])
      identity.append(row[1])

   #print certainty
   #print identity

   certainty = [float(i) for i in certainty] # Convert Certainty from string to float to allow sorting
   matrix = zip(certainty, identity) #combine them into a two dimentional list
   matrix.sort(key=itemgetter(0), reverse=True) #Sort Highest to Lowest Based on Certainty
   #Now Espeak the top three terms if they are > threshold
   print matrix [0]
   print matrix [1]
   print matrix [2]
   topthreeidentity = [x[1] for x in matrix[0:3]]
   topthreecertainty = [x[0] for x in matrix[0:3]]

   if topthreecertainty[0] > ConfigJetpacThreshold:
        FirstItem = str(topthreeidentity[0])
        print topthreecertainty[0], topthreeidentity[0]," 1st item Greater Than Threshold"
   else:
        FirstItem = "Nothing Recognized"
        print "Top item underthreshold"

   if topthreecertainty[1] > ConfigJetpacThreshold:
        SecondItem = str(topthreeidentity[1])
        print topthreecertainty[1], topthreeidentity[1], " 2nd item Greater Than Threshold"
   else:
        SecondItem =  " "
        print "Second Item Under Threshold"

   if topthreecertainty[2] > ConfigJetpacThreshold:
        ThirdItem = str(topthreeidentity[2])
        print topthreecertainty[2], topthreeidentity[2], " 3rd item Greater Than Threshold"
   else:
        ThirdItem = " "

   espeakstring = FirstItem + " " + SecondItem + " " + ThirdItem # read top three
   print espeakstring
   espeak_process = subprocess.Popen(["espeak",espeakstring, "--stdout"], stdout=subprocess.PIPE) #read the list out
   subprocess.Popen(["aplay", "-D", "sysdefault"], stdin=espeak_process.stdout, stdout=subprocess.PIPE) #Make it so no stuttering
   call (["sudo","rm","-rf","/dev/shm/classify.txt"]) #remove last run of classification info
camera.stop()
del(camera) # so that others can use the camera as soon as possible