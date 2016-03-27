import os #To set working directory properly
import re #import regular expression evaluator
import urllib #Used to test if internet is available
import time #required for sleep pauses
import threading #We will be making threads
import RPi.GPIO as GPIO #We use lots of GPIOs in this program
import datetime #To allow for keeping track of button press length
import subprocess #To launch external processes
import keyPress #Allow for asynchronous keyboard input lifted from http://stackoverflow.com/questions/510357/python-read-a-single-character-from-the-user
from subprocess import call #to launch external processes
import gaugette.rotary_encoder # Lets the rotation be handled with threaded watching
from webcamvideo import WebcamVideoStream #Class for creating a camera thread
from confmanager import ConfManager
from raspivoice import Raspivoice
from teradeep import Teradeep
from facedetect import Facedetect

GPIO.setmode(GPIO.BCM)  #setup for pinouts of the chip for GPIO calls. This will be different for the rotary encoder li$
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) #GPIO for detecting low battery
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Rotary Pushbutton Input
GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # GPIO for detecting Power Switch Position, used to shtudown system
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # GPIO for Detecting External Power State
GPIO.setup(20, GPIO.OUT)   #Define pin 20 as output, for vibration motor
pulses = 3 #make constant short pulses
for i in range(0,pulses):
        GPIO.output(20,True)
        time.sleep(0.05)
        GPIO.output (20,False)
        time.sleep(0.05)


espeak_process = subprocess.Popen(["espeak", "-f","/home/pi/introtext.txt", "--stdout"], stdout=subprocess.PIPE)
aplay_process = subprocess.Popen(["aplay", "-D", "sysdefault"], stdin=espeak_process.stdout, stdout=subprocess.PIPE)
aplay_process.wait() #Forces wait on initial disclaimer reading force wait for short introtext on second and subsequent boots

call (["sudo","cp","/home/pi/altgreet.txt","/home/pi/introtext.txt"]) #After first boot get rid of disclaimer and shorten the greeting


def CheckToClose(k, (keys, printLock)): #This is required for the keyscanning to use the USB number pad
    printLock.acquire()
    print "Close: " + k
    printLock.release()
    if k == "c":                        #While debugging. If you press 'c' once, you can now use ctrl c to terminate the execution
        keys.stopCapture()

t1=0 #t1-t4 used for timing pushbutton events
t2=0 # t2-t4 used as adders amongst a few intervals to allow for assignments of different functions based on time the button is depressed
t3=0 #
t4=0 #The final interval of 7 seconds shuts the device down (software, not electricity). It protects the filesystem and ought to remain

timesinceflip = 0

config = ConfManager() # Load our class with settings from aftersight.cfg

vibration = False #By default vibration is turned off

if config.ConfigVibrationStartup: #If the config file sets rangefinder/vibration for startup, toggle the variable for the vibration motor
        vibration = True

A_Pin=4 #Encoder CC direction
B_Pin=5 #Enconder C direction
encoder = gaugette.rotary_encoder.RotaryEncoder.Worker(A_Pin, B_Pin)#Use worker class to try to catch transitions better.
encoder.start()#start the worker class encoder watcher
encoder.steps_per_cycle = 4 #the encoder always gives 4 for 1 detente

oldexternalpowerstate = 0 # this variable enables an espeak event when the power plug is inserted or removed

Main=["Toggle Raspivoice","Toggle Teradeep","Toggle Distance Sensor","Toggle Face Detection", "Settings","acknowledgements","Disclaimer"]
Settings=["Advance Volume","Raspivoice Settings", "Teradeep Settings","Distance Sensor Settings","Update Software","Return to main menu"]
RaspivoiceSettings = ["Toggle Playback Speed","Toggle Blinders","Advance Zoom","Toggle Foveal Mapping", "Toggle Raspivoice Autostart", "Return to Main Menu"]
TeradeepSettings = ["Next Threshold",  "Toggle Teradeep Autostart","Return to Main Menu"]
DistanceSensorSettings = ["Cycle Feedback Method","Return to Main Menu"]
VolumeMenu = ["Volume Up", "Volume Down", "Return to Main Menu"]

#You can change and add menu items above, but you MUST go to the section where the MenuLevel and menupos are evaluated for a button press/release in under three seconds
#You have to change the actions for the items being evaluated there.
#If you don't, no bueno

bequiet = False #This is old and can be removed, but there is some conditional code below that would have to go at the same time. 
MenuLevel = Main #Select the Main Menu first
menupos = 0 #position in menu list

printLock = threading.Lock() #Setup for keyscanning thread
keys = keyPress.KeyCapture()
keys.startCapture(CheckToClose, (keys, printLock)) #Start the keyboard scanner thread

seconddelta = 0

call (["sudo","espeak","MainMenu,Rotate,Knob,For,Options"])
camera_port = 0 #Open Camera 0
#If your camera doesn't support HD, you'll have to change it here (1280X720)
camera = WebcamVideoStream(src=camera_port, width=640, height=480) #define where I dump camera input

camerastarted = False
raspi = Raspivoice(camera, config)
tera = Teradeep(camera, config)
face = Facedetect(camera, config)
cameraOk = camera.isOk() # Don't call this to often when the camera is stopped, since it will then temporarily init the camera to check it

if config.ConfigRaspivoiceStartup == True and cameraOk:

        camerastarted = camera.start()
        raspi.start()
if config.ConfigTeradeepStartup == True and cameraOk:
        if not camerastarted:
                camerastarted = camera.start()

        tera.start()
if not cameraOk:
	call (["sudo","espeak","No camera detected, check your connections."])

batteryshutdownstarttime = 0 #this will record the time when the shutdhown signal is first recieved
batteryshutdowndetectedflag = 0 #once the low battery signal has been detected once, this flag will stay true. This will avoid situations where the light is cycling
batteryshutdowntime = 300 #give the battery shutdown 300 seconds before forcing a shutdown

while 1:  #Main Loop
    if camera.cameraError and (raspi.running or tera.running):
    	camerastarted = False
    	raspi.stop()
    	tera.stop()
	face.stop()
    	call (["sudo","espeak","There was an error with the camera, stopping applications. Try reconnect the camera, and restart applications"])
    battstate = GPIO.input(27) #check if the battery low state is true or false
    switchstate = GPIO.input(9) #if the pushbutton is depressed, this ought to be true
    externalpowerstate = GPIO.input(10) #has external power been connected or disconnected
    CurrentMenuMaxSize = len(MenuLevel)-1 #Have to subtract one because lists start at zero, but the len function returns only natural numbers

    delta = encoder.get_delta()
    keysPressed  = keys.getAsync()
    #print keysPressed
    if (delta!=0 or keysPressed != []):
        print keysPressed
        #print "rotate %d" % delta

        #The Rotary Encoder has the annoying feature of giving back four delta steps per single detente ~usually~
        #For example, 1,1,1,1 is normal. Quite often it is 1,3 other times 1,2,1 or 1,1,2
        #Using the corrections below, rotations clockwise are normalized to a value of 1
        #Rotations counterclockwise are normalized to -1
        #So the normal output of 1,1,1,1 remains 1,3 becomes 1,1 and 1,2,1 or 1,1,2 become 1,1,1
        #The end result is that most often the values will be 2 or 3, and occasionally 4 after each rotation of one detente occurs
        #the seconddelta variable causes the menu item increase to only happen after the delta accumulates to 3.
        #By changing the top value for seconddelta, responsiveness for single increases changes
        #With a value of three, reliable operation happens

        if delta>0:
                delta=1
        if delta<0:
                delta=-1

        #print "corrected delta",delta
        if keysPressed == ['+']: #Simulate the outcome of rotary knob rotations to the right. Each time '+' is pressed it will act as though rotated cw
                seconddelta = 3
                delta = 1
        if keysPressed == ['-']:
                seconddelta = 3 #simulate the outcome of rotary knob rotations to the left. each time '-' is pressed it will act as though rotated ccw
                delta = -1
        if seconddelta == 3: #This was the most important value to change to get reliable single increments of the menu items
                seconddelta = 0
                menupos=menupos+delta
                print "MenuPosition" ,menupos
                print MenuLevel
                print "Current Menu Max Size",CurrentMenuMaxSize
                if menupos > CurrentMenuMaxSize: #when changing menu's, we set the position in the menu to a high value of 10. This way when the new menu is engaged the position is forced to the first item in the menu
                        menupos=0
                if menupos<0:
                        menupos=CurrentMenuMaxSize
                print (MenuLevel[menupos])
                if bequiet == False:
                        call(["sudo","killall","espeak"])
                        call(["sudo","espeak",MenuLevel[menupos]])
        elif seconddelta < 3:
                seconddelta = seconddelta + 1
    if (externalpowerstate != oldexternalpowerstate):
        print ('External Power State Changed')
        if(externalpowerstate == 1):
                call (["sudo","espeak","ExternalPowerConnected"])
        elif (externalpowerstate ==0):
                call (["sudo","espeak","ExternalPowerDisconnected"])
    if (switchstate == 1):
        #print ('Power Switch Turned Off, System Shutdown Initiated')
        call (["sudo", "espeak", "shutdown"])
        call (["sudo", "shutdown", "-h", "now"])
    #if (battstate == 1):
    #    print ('Battery OK, keep system up')
    if (config.ConfigBatteryShutdown == True):
	if (battstate == 1 and batteryshutdowndetectedflag == 1): #If the low power LED was on and then turned off again (the powerboost 1000c has this problem lots of detail here:https://forums.adafruit.com/viewtopic.php?f=8&t=88137 )
		batteryshutdowndetectedflag = 0 # Make the timer stop accumulating time when the state goes low again, the flag will be set and the timer will restart
		print ('Low Battery State Flipped killing timer') 
    if (config.ConfigBatteryShutdown == True):
	if (battstate == 0 and batteryshutdowndetectedflag == 0): #If the low battery state has changed from ok to low battery for the first time
		batteryshutdowndetectedflag = 1 #Flip the flag to true so we don't keep hearing about the low battery
		batteryshutdownstarttime = time.time() #Get the time when the countdown started
		print('Low Battery State Found, Starting Timer')
    if (batteryshutdowndetectedflag == 1): #The next time it loops through it will come here because the flag has been changed to true
		batterytimesinceshutdownstarted = time.time() - batteryshutdownstarttime #This value will start returning an increasing number of seconds since the shutdown timer started
		if (batterytimesinceshutdownstarted >= batteryshutdowntime): #if it exceeds 300 seconds...
			call(["sudo","espeak","LowBatteryDetectedForFiveMinutesPleaseShutDownOrAddExternalPower"])
			batteryshutdowndetectedflag = 0 #reset the 300 second timer, this means if nothing changes the user is reminded every five minutes to shut down
		 
    if GPIO.input(25):
        #print('Button Released')
        if (t3 < 3 and t3 > 0 or keysPressed == ['\r']): #If the button is released in under 3 seconds, execute the command for the currently selected menu and function
                print "Detected Button Release in less than 3 seconds"
                if bequiet == False:
                #Main=["Launch Raspivoice","Launch Teradeep","Toggle Distance Sensor","Toggle Facial Detection", "Settings","acknowledgements","Disclaimer"]
                        if (MenuLevel == Main and menupos == 0): #1st option in main menu list is launch raspivoice
                                if (not raspi.running):
                                        
                                        if (not camerastarted):

                                                camerastarted = camera.start()
                                                if not camerastarted:
                                                	call (["sudo","espeak","No camera detected, not Starting RaspiVoice"])
                                                else:
												call (["sudo","espeak","Starting RaspiVoice"])
												raspi.start()
                                        else:
                                        	call (["sudo","espeak","Starting RaspiVoice"])
                                        	raspi.start()
                                else:
                                        call (["sudo","espeak","Stopping RaspiVoice"])
                                        if (not tera.running or not face.running):
                                                camera.stop()
                                                camerastarted = False

                                        raspi.stop()


                        if (MenuLevel == Main and menupos == 1):
                                if (not tera.running):
                                        if (not camerastarted):
                                                camerastarted = camera.start()
                                                if not camerastarted:
                                                	call (["sudo","espeak","No camera detected, not Starting Teradeep"])
                                                else:
												call (["sudo","espeak","Starting Teradeep"])
												tera.start()
                                        else:
                                        	call (["sudo","espeak","Starting Teradeep"])
                                        	tera.start()

                                else:
                                        call (["sudo","espeak","Stopping Teradeep"])
                                        if (not raspi.running or not face.running):
                                                camera.stop()
                                                camerastarted = False

                                        tera.stop()



                        if (MenuLevel == Main and menupos == 2): 
                                if vibration == True:
                                        call (["sudo","espeak","DistanceSensorToggledOff"])
                                        call (["sudo","killall","rangefinder"])
					GPIO.output (20,False) #If rangefinder.py exited with the vibrator on, this offs it
                                        vibration = False
                                else:
                                        if config.ConfigAudibleDistance == True:
                                                call(["sudo","espeak","EnglishDistanceSelectedOtherfeedbackUnavailable"])
                                        else:
                                                call (["sudo","espeak","DistanceSensorToggledOn"])
                                                subprocess.Popen(["sudo","python","/home/pi/rangefinder.py"])
                                                vibration = True
			if (MenuLevel == Main and menupos ==3): #Toggle Facial Detection
				if (not face.running):

                                        if (not camerastarted):

                                                camerastarted = camera.start()
                                                if not camerastarted:
                                                        call (["sudo","espeak","No camera detected, not Starting Facial Detection"])
                                                else:
                                                                                                call (["sudo","espeak","Starting Facial Detection"])
                                                                                                face.start()
                                        else:
                                                call (["sudo","espeak","Starting Facial Detection"])
                                                face.start()
                                else:
                                        call (["sudo","espeak","Stopping Facial Detection"])
                                        if (not tera.running or not raspi.running):
                                                camera.stop()
                                                camerastarted = False

                                        face.stop()

                        if (MenuLevel == Main and menupos == 4): #Enter The Settings Menu
                                MenuLevel = Settings
                                call (["sudo","espeak","ChangeSettings"])
                                menupos = 10
                        if (MenuLevel == Main and menupos == 4):
                                espeak_process = subprocess.Popen(["espeak", "-f","/home/pi/acknowledgements.txt", "--stdout"], stdout=subprocess.PIPE)
                                subprocess.Popen(["aplay", "-D", "sysdefault"], stdin=espeak_process.stdout, stdout=subprocess.PIPE)
                        if (MenuLevel == Main and menupos == 5):
                                espeak_process = subprocess.Popen(["espeak", "-f","/home/pi/disclaimer.txt", "--stdout"], stdout=subprocess.PIPE)
                                subprocess.Popen(["aplay", "-D", "sysdefault"], stdin=espeak_process.stdout, stdout=subprocess.PIPE)
                #Settings=["Advance Volume","Raspivoice Settings", "Teradeep Settings","Distance Sensor Settings", "Toggle low battery shutdown", "Return to main menu"]
                        if (MenuLevel == Settings and menupos == 0):
                                commandlinevolume = int(config.ConfigVolume)
                                commandlinevolume = commandlinevolume + 10
                                if commandlinevolume > 100: #Wrap volume back to lowest setting
                                        config.ConfigVolume = "70"
                                        commandlinevolume = 70 #lowest setting
                                if commandlinevolume == 70:
                                        fakevolume = 10 #lowest setting said as 10%
                                if commandlinevolume == 80:
                                        fakevolume = 50 #next setting said as 50%
                                if commandlinevolume == 90:
                                        fakevolume = 75 #next setting said as 75%
                                if commandlinevolume == 100:
                                        fakevolume = 100 #next setting said as 100%
                                fakevolume = str(fakevolume)
                                call (["sudo","espeak","ChangingVolumeTo"])
                                call (["sudo","espeak",fakevolume])
                                call (["sudo","espeak","Percent"])
                                volumearg = config.ConfigVolume + "%"
                                call (["sudo","amixer","sset","PCM,0",volumearg])
                                config.ConfigVolume = str(commandlinevolume)
                                menupos = 0 #keep menu position on advance volume to allow for repeated presses
                        if (MenuLevel == Settings and menupos == 1):
                                MenuLevel = RaspivoiceSettings
                                call (["sudo","espeak","RaspivoiceSettings"])
                                menupos = 10
                        if (MenuLevel == Settings and menupos == 2):
                                MenuLevel = TeradeepSettings
                                call (["sudo","espeak","TeradeepSettings"])
                                menupos = 10
                        if (MenuLevel == Settings and menupos == 3):
				MenuLevel = DistanceSensorSettings
				call(["sudo","espeak","DistanceSensorSettings"])
				menupos = 10
                        if (MenuLevel == Settings and menupos == 4):
				if (externalpowerstate == 1):
					call(["sudo","espeak","PleaseLeaveExternalPowerConnectedUntilUpdatesAreComplete"])
					call(["sudo","espeak","ShuttingDownProgramsForUpdateProcedure"])
					face.stop()
					tera.stop()
					raspi.stop()
					call(["sudo","killall","rangefinder"])
					call(["sudo", "espeak", "ProgramsTerminatedDetectingInternetConnection"])
					try:
						github="https://www.github.com"
						data = urllib.urlopen(github) #Check if github.com can be connected to. That is where our files are stored
						call(["sudo","espeak","InternetConnectionAvailableGithubAvailable"])
						inet=1
					except:
						call(["sudo","espeak","InternetConnectionNotAvailableAndOrGithubIsDown"])
						inet=0
					if (inet == 1): #If internet is available then sync the local git directory with remote
						currentversionstring = "Number" + str(config.ConfigUpdateNumber)
						call(["sudo","espeak","CurrentUpdateIs"+currentversionstring])
						call(["sudo","espeak","DownloadingAvailableUpdate"])
						call(["sudo","/home/pi/./a-update.sh"])
						call(["sudo","espeak","Updates Downloaded"])
						call(["sudo","espeak","ComparingUpdateNumber"])
						NewVersionNumberString = subprocess.Popen(['grep', 'updatenumber', '/home/pi/After-Sight-Model-1/aftersight.cfg'], stdout=subprocess.PIPE).communicate()[0]
						NewVersionNumber = map(int, re.findall('\d+',NewVersionNumberString))
						NewVersionNumber = int(NewVersionNumber[0]) #this is weird but the regular expression put the item into a list with a size of 1
						print "new Update Number is "+str(NewVersionNumber) #that made it so you couldn't compare the new version number to the integer value of the current version number
						print "Current Version Number is" + str(config.ConfigUpdateNumber)
						call(["sudo","espeak","NewUpdateNumberis"+str(NewVersionNumber)])
						if (NewVersionNumber > config.ConfigUpdateNumber):
							call(["sudo","espeak","NewUpdateFoundPerformingUpdate"])
							call(["sudo","cp","-rf","/home/pi/After-Sight-Model-1/installdeps.sh", "/home/pi/installdeps.sh"])
							call(["sudo","espeak","InstallingDependencies"])
							call(["sudo","/home/pi/installdeps.sh"])
							call(["sudo","DependenciesInstalled"])
							call(["sudo","espeak","ReplacingCore"])
							os.chdir("/home/pi/After-Sight-Model-1")
							call(["sudo","./a-update_core.sh"])
							call(["sudo","espeak","RebuildingRaspivoice"])
							os.chdir("/home/pi/After-Sight-Model-1")
							call(["sudo","./a-update_voice.sh"])
							call(["sudo","espeak","RebuildingTeradeep"])
                	                                os.chdir("/home/pi/After-Sight-Model-1")
							call(["sudo","./a-update_teradeep.sh"])
							call(["sudo","espeak","RebuildingFacialDetection"])
                                        	        os.chdir("/home/pi/After-Sight-Model-1")
							call(["sudo","./a-update_facedetect.sh"])
							call(["sudo","RunningOneTimeScripts"])
							#one time script evaluator NEW UPDATES REQUIRE aftersight.cfg ConfigUpdateNumber to be incremented EVEN IF YOU DON'T MAKE A ONE TIME SCRIPT. Creat the folder for it under /home/pi/After-Sight-Model-1/updatecontrol/updateX and make update.sh script in the numbered folder it doesn't have to do anything. Just put it there
							files = os.listdir('/home/pi/After-Sight-Model-1/updatecontrol')
							unsortednumberlist = [] #the folder list returned by the os.listdir command are not sorted by number, we will use regular expression to get the numbers in a list, then sort them
							for file in files:
								VersionNumber = map(int, re.findall('\d+',file))
								unsortednumberlist.extend(VersionNumber) #use extend - this makes all elements in one list. append makes a list of lists
    								print(file)
							print unsortednumberlist
							unsortednumberlist.sort(key=int) #this sorts the number list
							print unsortednumberlist
							for number in unsortednumberlist: #now step through the list. If the number is higher than the current version number, execute the script in /home/pi/After-Sight-Model-1/updatecontrol/updateX/update.sh
								if number > config.ConfigUpdateNumber:
									call(["sudo","espeak","ApplyingUpdateNumber"+str(number)])
									executescriptstring = "/home/pi/After-Sight-Model-1/updatecontrol/update" + str(number) +"/update.sh"
									call(["sudo",executescriptstring])
								else:
									call(["sudo","espeak","UpdateNumber"+str(number)+"AlreadyInstalled"])	
							call(["sudo","espeak","UpdateCompletedRebootRequired"])
							call(["sudo","shutdown","-r","now"])
					else:
						call(["sudo","espeak","NoNewVersionNoUpdateRequired"])
					menupos = 10				
				else:
					call(["sudo","espeak","ExternalPowerMustBeConnectedForUpdatePlugInAndTryAgain"])
				menupos = 10
			if (MenuLevel == Settings and menupos == 5):
                                MenuLevel = Main
                                call (["sudo","espeak","MainMenu"])
                                menupos = 10
                 #RaspivoiceSettings = ["Toggle Playback Speed", "Toggle Blinder","Advance Zoom","Toggle Foveal Mapping","Toggle Raspivoice Autostart", "Return to Main Menu"]
                        if (MenuLevel == RaspivoiceSettings and menupos == 0):
                                if config.ConfigRaspivoicePlaybackSpeed  == "--total_time_s=1.05":
                                        call (["sudo","espeak","ChangedToFast"])
                                        config.ConfigRaspivoicePlaybackSpeed = "--total_time_s=0.5"
                                elif config.ConfigRaspivoicePlaybackSpeed == "--total_time_s=0.5":
                                        call (["sudo","espeak","ChangedToSlow"])
                                        config.ConfigRaspivoicePlaybackSpeed = "--total_time_s=2.0"
                                else:
                                        call (["sudo","espeak","ChangedToNormal"])
                                        config.ConfigRaspivoicePlaybackSpeed = "--total_time_s=1.05"
                                menupos = 0 #Keep at playback speed setting to allow repeated toggle
                                raspi.restart() # We want to relaunch raspivoce when we change this, ignored if not running
                        if (MenuLevel == RaspivoiceSettings and menupos == 1):
                                if config.ConfigBlinders == "--blinders=0":
                                        call (["sudo","espeak","BlinderEnabled"])
                                        config.ConfigBlinders = "--blinders=50"
                                else:
                                        call(["sudo","espeak","BlindersDisabled"])
                                        config.ConfigBlinders = "--blinders=0"
                                raspi.restart()#We must relaunch raspivoice when we change this.
                        if (MenuLevel == RaspivoiceSettings and menupos == 2):
                                if config.ConfigZoom == "--zoom=1.0":
                                        call (["sudo","espeak","ZoomChangedTo150Percent"])
                                        config.ConfigZoom = "--zoom=1.5"
                                elif config.ConfigZoom == "--zoom=1.5":
                                        call (["sudo","espeak","ZoomChangedTo200Percent"])
                                        config.ConfigZoom = "--zoom=2.0"
                                else:
                                        call (["sudo","espeak","ZoomTurnedOff"])
                                        config.ConfigZoom = "--zoom=1.0"
                                raspi.restart() #Restart Raspivoice with the new settings
                        if (MenuLevel == RaspivoiceSettings and menupos == 3):
                                if config.ConfigFovealmapping == "--foveal_mapping":
                                        call (["sudo","espeak","FovealMappingDisabled"])
                                        config.ConfigFovealmapping = "--verbose" #I had to use something here. leaving it as " " or "" wrecked things
                                else:
                                        call (["sudo","espeak","FovealMappingEnabled"])
                                        config.ConfigFovealmapping = "--foveal_mapping"
                                raspi.restart()#Restart Raspivoice with the new settings
                        if (MenuLevel == RaspivoiceSettings and menupos == 4):
                                if config.ConfigRaspivoiceStartup == True:
                                        call (["sudo","espeak","NoLaunchOnStartup"])
                                        config.ConfigRaspivoiceStartup = False
                                else:
                                        call (["sudo","espeak","RaspivoiceWillAutostart"])
                                        config.ConfigRaspivoiceStartup = True
                        if (MenuLevel == RaspivoiceSettings and menupos == 5):
                                MenuLevel = Main
                                menupos = 10
                                config.save()
                                call (["sudo","espeak","Main Menu"])
                #TeradeepSettings = ["Next Threshold", "Toggle Teradeep Autostart","Return to Main Menu"]

                        if (MenuLevel == TeradeepSettings and menupos == 0):
                                if config.ConfigTeradeepThreshold == "2":
                                        call (["sudo","espeak","Changing To 5%"]) #somewhat stringent
                                        config.ConfigTeradeepThreshold = "5"
                                elif config.ConfigTeradeepThreshold == "5":
                                        call (["sudo","espeak","ChangingTo10%"])
                                        config.ConfigTeradeepThreshold = "10"            #More Stringent
                                elif config.ConfigTeradeepThreshold == "10":
                                        call (["sudo","espeak","ChangingTo15%"])
                                        config.ConfigTeradeepThreshold = "15"           #More Stringent
                                elif config.ConfigTeradeepThreshold == "15":
                                        call (["sudo","espeak","ChangingTo20%"])
                                        config.ConfigTeradeepThreshold = "20"
                                else:
                                        call (["sudo","espeak","Changingto2%"])
                                        config.ConfigTeradeepThreshold = "2"            #Most stringent
                        if (MenuLevel == TeradeepSettings and menupos == 1):
                                if config.ConfigTeradeepStartup == True:
                                        call (["sudo","espeak","NoLaunchOnStartup"])
                                        config.ConfigTeradeepStartup = False
                                else:
                                        call (["sudo","espeak","TeradeepWillAutostart"])
                                        config.ConfigTeradeepStartup = True
                        if (MenuLevel == TeradeepSettings and menupos == 2):
                                config.save()
                                MenuLevel = Main
                                call (["sudo","espeak","Main Menu"])
                                menupos = 10
			#DistanceSensorSettings = ["Cycle Feedback Method","Return to Main Menu"]
			if (MenuLevel == DistanceSensorSettings and menupos == 0):
				if config.ConfigVibrationEnabled == True:
					config.ConfigVibrationEnabled = False
					config.ConfigVibrateSoundEnabled = True
					call (["sudo","espeak","VibrationFeedbackDisabledToneFeedbackEnabled"])
				elif config.ConfigVibrateSoundEnabled == True:
					config.ConfigVibrateSoundEnabled = False
					config.ConfigAudibleSitance = True
					call(["sudo","espeak","ToneFeedbackDisabledEnglishFeedbackEnabledLaunchTeradeepToUse"])
				else:
					config.ConfigAudibleDistance = False
					config.ConfigVibrationEnabled = True
					call (["sudo","espeak","EnglishFeedbackDisabledVibrationEnabled"])
			if (MenuLevel == DistanceSensorSettings and menupos == 1):
				config.save()
				MenuLevel = Main
				call (["sudo","espeak","Main Menu"])
                                menupos = 10

        t1=0 #Reset the timers
        t2=0
        t3=0
        t4=0
    elif t1 == 0:
        t1 = time.time() #clock value when button pressed in
    elif (t1 > 1 and t3 < 3):
        t2 = time.time() #clock value at current moment While the button has been pressed in
        t3 = t2 - t1 #difference from initial press time to current moment
        print ">1<3",t3
    elif (t3 > 3 and t3 <4):
        print ">3<4",t3
#	Although we got rid of killing processes here, we can re-use this area for some function relating to a 3-4 second button press. Perhaps there is some equivalent of a sleep command we can use on the device to save battery power that can use a gpio pin interrupt to wake up from?
        t3 = 5.1
        t4=5.1
    elif (t4 > 4 and t4 < 7):
        t2=time.time()
        t4 = t2+1 - t1
    elif t4 > 7:
        print "shutdown",t4
        call (["sudo", "shutdown", "-h", "now"])
        call (["sudo", "espeak","Shutdown"])
        exit
    oldexternalpowerstate = externalpowerstate #This captures the current external power state to compare when the loop runs next. critical for knowing when power is plugged in or unplugged
