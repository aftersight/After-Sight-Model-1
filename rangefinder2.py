import time
import RPi.GPIO as GPIO
import serial
import datetime
from subprocess import call

time.sleep(5) #This sleep spot is meant to let the preamble espeak for raspivoice finish with less intrusion from this process.
GPIO.setmode(GPIO.BCM)  #setup for PWM
GPIO.setup(20, GPIO.OUT)   #Define pin 20 as output, for PWM modulation of vibration motor
p = GPIO.PWM(20, 25)  #channel = 20 , frequency = 25 hz
p.start(5) #5% duty cycle to start. should immediately change as the rangefinder reads
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) #GPIO for detecting low battery
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Rotary Pushbutton Input
GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # GPIO for detecting Power Switch Position, used to shtudown system
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # GPIO for Detecting External Power State
maxbotix = serial.Serial("/dev/ttyAMA0",baudrate=9600,timeout=5) #Open a serial input to recieve from the maxbotix ultrasonic sensor
time.sleep(0.2)#This sleep interval is required to let the serial input open completely before it is read for the first time. Without this pause, random crashes on startup occur
t1=0 #t1-t4 used for timing pushbutton events
t2=0
t3=0
t4=0
vibration=-1 #vibration starts off. Changing this = 1 starts vibration based on distance measurement
timesinceflip = 0
oldexternalpowerstate = 0 # this variable enables an espeak event when the power plug is inserted or removed
while 1:
    maxbotix.flushInput() #clear buffer to get fresh values if you don't do this, you won't get responsive readings
    currdistance = maxbotix.readline(10) #Take ten characters worth of the serial buffer that accumulates since the flush
    stripstart = currdistance.find("R") #Look for the character "R", find out where it occurs in the string first
    stripend = stripstart + 5 #Define the end of the character length we need to grab the numeric info
    currdistance = currdistance[stripstart+1:stripend] #strip out the numeric info
    currmm = float(currdistance) #Now make the info a number instead of a string
    print currmm #comment this out after debugging
    battstate = GPIO.input(27)
    switchstate = GPIO.input(9)
    externalpowerstate = GPIO.input(10)
    if (externalpowerstate != oldexternalpowerstate):
        print ('External Power State Changed')
        if(externalpowerstate == 1):
                print ('External Power Connected')
                call (["sudo","espeak","ExternalPowerConnected"])
        elif (externalpowerstate ==0):
                print ('External Power Disconnected')
                call (["sudo","espeak","ExternalPowerDisconnected"])
    if (externalpowerstate == 0):
        print ('External Power Disconnected, Running from Internal Battery')
    if (switchstate == 1):
        print ('Power Switch Turned Off, System Shutdown Initiated')
        call (["sudo", "espeak", "shutdown"])
        call (["sudo", "shutdown", "-h", "now"])
    if (switchstate == 0):
        print ('Power Switch Is On, Keep Working')
    if (battstate == 1):
        print ('Battery OK, keep system up')
    if (battstate == 0):
        print ('Battery Low, System Shutdown')
    if (vibration == 1):
        #print "vibration on"
        if (currmm > 300 and currmm < 600):
                p.ChangeFrequency(5)
                p.ChangeDutyCycle(50)
        if (currmm > 600 and currmm < 1000):
                p.ChangeFrequency(7)
                p.ChangeDutyCycle(50)
        if (currmm > 1000 and currmm < 2000):
                p.ChangeFrequency(10)
                p.ChangeDutyCycle(50)
        if (currmm > 2000 and currmm < 3000):
                p.ChangeFrequency(20)
                p.ChangeDutyCycle(50)
        if (currmm > 3000 and currmm < 4000):
                p.ChangeFrequency(30)
                p.ChangeDutyCycle(50)
        if currmm > 4000:
                p.ChangeFrequency(40)
                p.ChangeDutyCycle(50)
    elif (vibration == -1):
        p.ChangeDutyCycle(0)
        #print "Vibration Off
    if GPIO.input(25):
        #print('Button Released')
        #print vibration
        t1=0
        t2=0
        t3=0
        t4=0
    elif t1 == 0:
        t1 = time.time()
    elif (t1 > 1 and t3 < 3):
        t2 = time.time()
        t3 = t2 - t1
        print ">1<3",t3
    elif (t3 > 3 and t3 <4):
        print ">3<4",t3
        vibration = -vibration
        t3 = 5.1
        t4=5.1
        #print "Vibration Flipped"
        #print "=5.1",t4
    elif (t4 > 4 and t4 < 7):
        t2=time.time()
        t4 = t2+1 - t1
        #print ">4<7",t4
        #print "between vibration change and shutdown"
    elif t4 > 7:
        p.ChangeDutyCycle(0)
        print "shutdown",t4
        call (["sudo", "shutdown", "-h", "now"])
        call (["sudo", "espeak","Shutdown"])
        exit
    oldexternalpowerstate = externalpowerstate #This captures the current external power state to compare when the loop runs next. critical for knowing when power is plugged in or unplugged
