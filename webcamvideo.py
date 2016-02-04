# import the necessary packages
from threading import Thread
import cv2
import os

class WebcamVideoStream:
	def __init__(self, src=0, width=1280, height=720):
		self.width = width
		self.height = height
		self.src = src
		self.stream = None
		# initialize the variable used to indicate if the thread should
		# be stopped
		self.stopped = False
		self.videoFile = "/dev/video" + str(src)
		self.cameraError = False

	def start(self):
		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(self.src)

		if not self.stream.isOpened():
			self.cameraError = True
			return False

		self.cameraError = False
		self.stream.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, self.width)
		self.stream.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, self.height)
		(self.grabbed, self.frame) = self.stream.read()


		# start the thread to read frames from the video stream

		self.stopped = False
		Thread(target=self.update, args=()).start()
		return True

	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				self.stream.release()
				self.stream = None
				return

			# otherwise, read the next frame from the stream
			(self.grabbed, self.frame) = self.stream.read()


	def read(self):
		# If someone unplugs the camera, it seems that the internal structures don't notice, we only get error to the console.
		# Therefore, we check if the video device is present, and if not we flag the error and stop the camera thread, which will release the internal structures
		# We return the last frame regardless, so that no-one crashes
		if not os.path.exists(self.videoFile) or not self.grabbed:
			self.cameraError = True
			self.stop()
		# return the frame most recently read
		return self.frame

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
	def isOk(self):
		if not self.stream == None:
			return self.stream.isOpened()
		else:
			stream = cv2.VideoCapture(self.src) # temporarily init the camera to check if its Ok
			status = stream.isOpened()
			stream.release()
			return status


