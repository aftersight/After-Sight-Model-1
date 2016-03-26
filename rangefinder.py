import time
import RPi.GPIO as GPIO
import serial
import datetime
from subprocess import call
import setproctitle
import pyaudio
import numpy as np
from confmanager import ConfManager

setproctitle.setproctitle("rangefinder")

GPIO.setmode(GPIO.BCM)  #setup for PWM
GPIO.setup(20, GPIO.OUT)   #Define pin 20 as output
maxbotix = serial.Serial("/dev/ttyAMA0",baudrate=9600,timeout=5) #Open a serial input to recieve from the maxbotix ultrasonic sensor
time.sleep(0.2)#This sleep interval is required to let the serial input open completely before it is read for the first time. Without this pause, random crashes on startup occur
timesinceflip = 0

config = ConfManager()

print config.ConfigVibrationEnabled
print config.ConfigVibrateSoundEnabled

p = pyaudio.PyAudio()

volume = 0.2 # Range 0.0 - 1.0
fs = 44100 #Audio Sampling Rate
duration = 0.5 #Duration in seconds, may be float
f = 440  #Sine Frequency, Hz, may be float
#Generate Samples, Not Conversion to float32 array
samples = (np.sin(2*np.pi*np.arange(fs*duration)*f/fs)).astype(np.float32)

#for paFloat32 sample values must be in range -1.0 = 1.0
stream = p.open(format = pyaudio.paFloat32, channels = 1, rate = fs, output = True)
#Play
stream.write(volume*samples)
stream.stop_stream()
stream.close()

while 1:
    maxbotix.flushInput() #clear buffer to get fresh values if you don't do this, you won't get responsive readings
    currdistance = maxbotix.readline(10) #Take ten characters worth of the serial buffer that accumulates since the flush
    stripstart = currdistance.find("R") #Look for the character "R", find out where it occurs in the string first
    stripend = stripstart + 5 #Define the end of the character length we need to grab the numeric info
    currdistance = currdistance[stripstart+1:stripend] #strip out the numeric info
    currmm = float(currdistance) #Now make the info a number instead of a string
    print currmm #comment this out after debugging
    if (currmm > 299 and currmm < 600):
        pulses = 20 #make constant short pulses
        print "should be checking if vibrate or tweet"
        if config.ConfigVibrateSoundEnabled == "True":
                f = 9000
                samples = (np.sin(2*np.pi*np.arange(fs*duration)*f/fs)).astype(np.float32)
                stream = p.open(format = pyaudio.paFloat32, channels = 1, rate = fs, output = True)
                #Play
                print "Should be tweeting"
                stream.write(volume*samples)
        if config.ConfigVibrationEnabled == "True":
                print "Should be vibrating"
                for i in range(0,pulses):
                        GPIO.output(20,True)
                        time.sleep(0.01)
                        GPIO.output (20,False)
                        time.sleep(0.01)
        if config.ConfigVibrateSoundEnabled == "True":
                stream.stop_stream()
                stream.close()
    elif (currmm > 600 and currmm < 1000):
        pulses = 10 #make constant short pulses
        if config.ConfigVibrateSoundEnabled == "True":
                f = 8500
                samples = (np.sin(2*np.pi*np.arange(fs*duration)*f/fs)).astype(np.float32)
                stream = p.open(format = pyaudio.paFloat32, channels = 1, rate = fs, output = True)
                #Play
                stream.write(volume*samples)
                print "should be tweeting"
        if config.ConfigVibrationEnabled == "True":
                print "should be vibrating"
                for i in range (0,pulses):
                        GPIO.output(20,True)
                        time.sleep(0.01)
                        GPIO.output (20,False)
                        time.sleep(0.01)
        if config.ConfigVibrateSoundEnabled == "True":
                stream.stop_stream()
                stream.close()
    elif (currmm > 1000 and currmm < 2000):
        pulses = 8 #make constant short pulses
        if config.ConfigVibrateSoundEnabled == "True":
                f = 8000
                samples = (np.sin(2*np.pi*np.arange(fs*duration)*f/fs)).astype(np.float32)
                stream = p.open(format = pyaudio.paFloat32, channels = 1, rate = fs, output = True)
                #Play
                stream.write(volume*samples)
        if config.ConfigVibrationEnabled == "True":
                for i in range(0,pulses):
                        GPIO.output(20,True)
                        time.sleep(0.01)
                        GPIO.output (20,False)
                        time.sleep(0.01)
        if config.ConfigVibrateSoundEnabled == "True":
                stream.stop_stream()
                stream.close()
    elif (currmm > 2000 and currmm < 3000):
        pulses = 5 #make constant short pulses
        if config.ConfigVibrateSoundEnabled == "True":
                f = 7750
                samples = (np.sin(2*np.pi*np.arange(fs*duration)*f/fs)).astype(np.float32)
                stream = p.open(format = pyaudio.paFloat32, channels = 1, rate = fs, output = True)
                #Play
                stream.write(volume*samples)
        if config.ConfigVibrationEnabled == "True":
                for i in range(0,pulses):
                        GPIO.output(20,True)
                        time.sleep(0.01)
                        GPIO.output (20,False)
                        time.sleep(0.01)
        if config.ConfigVibrateSoundEnabled == "True":
                stream.stop_stream()
                stream.close()
    elif (currmm > 3000 and currmm < 4000):
        pulses = 3 #make constant short pulses
        if config.ConfigVibrateSoundEnabled == "True":
                f = 7500
                samples = (np.sin(2*np.pi*np.arange(fs*duration)*f/fs)).astype(np.float32)
                stream = p.open(format = pyaudio.paFloat32, channels = 1, rate = fs, output = True)
                #Play
                stream.write(volume*samples)
        if config.ConfigVibrationEnabled == "True":
                for i in range(0,pulses):
                        GPIO.output(20,True)
                        time.sleep(0.01)
                        GPIO.output (20,False)
                        time.sleep(0.01)
        if config.ConfigVibrateSoundEnabled == "True":
                stream.stop_stream()
                stream.close()

    elif currmm > 4000:
        pulses = 2 #make constant short pulses
        if config.ConfigVibrateSoundEnabled == "True":
                f = 7250
                samples = (np.sin(2*np.pi*np.arange(fs*duration)*f/fs)).astype(np.float32)
                stream = p.open(format = pyaudio.paFloat32, channels = 1, rate = fs, output = True)
                #Play
                stream.write(volume*samples)
        if config.ConfigVibrationEnabled == "True":
                for i in range(0,pulses):
                        GPIO.output(20,True)
                        time.sleep(0.01)
                        GPIO.output (20,False)
                        time.sleep(0.01)
        if config.ConfigVibrateSoundEnabled == "True":
                stream.stop_stream()
                stream.close()

    else:
        pulses = 1 #make constant short pulses
        if config.ConfigVibrateSoundEnabled == "True":
                f = 7000
                samples = (np.sin(2*np.pi*np.arange(fs*duration)*f/fs)).astype(np.float32)
                stream = p.open(format = pyaudio.paFloat32, channels = 1, rate = fs, output = True)
                #Play
                stream.write(volume*samples)
        if config.ConfigVibrationEnabled == "True":
                for i in range (0,pulses):
                        GPIO.output(20,True)
                        time.sleep(0.01)
                        GPIO.output (20,False)
                        time.sleep(0.01)
        if config.ConfigVibrateSoundEnabled == "True":
                stream.stop_stream()
                stream.close()

    time.sleep(0.05)