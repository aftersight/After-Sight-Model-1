# USAGE
# python cam.py --face cascades/haarcascade_frontalface_default.xml
# python cam.py --face cascades/haarcascade_frontalface_default.xml --video video/adrian_face.mov

# import the necessary packages
import setproctitle
from pyimagesearch.facedetector import FaceDetector
from pyimagesearch import imutils
import argparse
import cv2
import time
import os
from subprocess import call

setproctitle.setproctitle("FacialDetectProcess")
# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-f", "--face", required = True,
	help = "path to where the face cascade resides")
args = vars(ap.parse_args())

faceimg = "/dev/shm/face.jpg"
facetext = "/dev/shm/face_text"
facelocation = "/dev/shm/face.txt"
faceframe = "/dev/shm/face_frame"
# construct the face detector
fd = FaceDetector(args["face"])

# keep looping
while True:
	if (os.path.exists(faceframe)):
		fX = 0
		fY = 0
		fW = 0
		fH = 0

		# grab the current frame
		print "reading image"
		gray = cv2.imread('/dev/shm/face.jpg',0)
		height, width = gray.shape #get resolution for plotting location to screen thirds in facedetect.py
		# detect faces in the image and then clone the frame
		# so that we can draw on it
		print "making face detect rectangle"
		faceRects = fd.detect(gray, scaleFactor = 1.1, minNeighbors = 5,
			minSize = (30, 30))

		# loop over the face bounding boxes and draw them
		for (fX, fY, fW, fH) in faceRects:
			cv2.rectangle(gray, (fX, fY), (fX + fW, fY + fH), (0, 255, 0), 2)
		print "Rectangle" + str(fX) + str(fY) + str(fW) + str(fH)
		#Write rectangle to file for processing by facedetect.py
		print "writing rectangle parameters to file"
		if (os.path.exists(facelocation)):
			os.remove(facelocation)	
		with open(facelocation,'w') as f:
			f.write(str(fX)+",")
			f.write(str(fY)+",")
			f.write(str(fW)+",")
			f.write(str(fH)+",")
			f.write(str(height)+",")
			f.write(str(width))
		f.close()
		#create a file 'face_text' as a signal to the face.txt reading portion
		if (os.path.exists(facetext)):
			os.remove(facetext)
		os.mknod(facetext)
		print "removing face_frame to stimulate the next image generation." 
		os.remove(faceframe)
	else:
		print "No frame available for analysis"
		time.sleep(0.2)


# cleanup the camera and close any open windows
#camera.release()
cv2.destroyAllWindows()
