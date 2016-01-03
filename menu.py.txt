import time #required for sleep pauses
import RPi.GPIO as GPIO #We use lots of GPIOs in this program
import datetime #To allow for keeping track of button press length
import subprocess #To launch external processes
from subprocess import call #Same reasons
import gaugette.rotary_encoder # Lets the rotation be handled with threaded watching
import ConfigParser # Lets us user aftersight.cfg easily


call (["sudo","cp","/home/pi/altgreet.txt","/home/pi/introtext.txt"])

GPIO.setmode(GPIO.BCM)  #setup for pinouts of the chip for GPIO calls. This will be different for the rotary encoder library definitions which have to use wiringpi
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) #GPIO for detecting low battery
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Rotary Pushbutton Input
GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # GPIO for detecting Power Switch Position, used to shtudown system
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # GPIO for Detecting External Power State

t1=0 #t1-t4 used for timing pushbutton events
t2=0 # t2-t4 used as adders amongst a few intervals to allow for assignments of different functions based on time the button is depressed
t3=0 #
t4=0 #The final interval of 7 seconds shuts the device down (software, not electricity). It protects the filesystem and ought to remain

timesinceflip = 0
GPIO.setup(20, GPIO.OUT)   #Define pin 20 as output, for PWM modulation of vibration motor
p = GPIO.PWM(20, 25) #Set some initial value to give it a wiggle
p.start(5)
p.ChangeDutyCycle(0)#then shut it off


#Use ConfigParser to Read Persistent Variables from AfterSight.CFG

Config = ConfigParser.RawConfigParser() #set variable to read config into
Config.read('aftersight.cfg') #read from aftersight.cfg

ConfigVolume = Config.get('AfterSightConfigSettings','configvolume') #volume setting percentage
ConfigRaspivoiceStartup = Config.get('AfterSightConfigSettings','configraspivoicestartup') #Does raspivoice execute on startup? Boolean True/False
ConfigJetpacStartup = Config.get('AfterSightConfigSettings','configjetpacstartup') #Does Jetpac execute on startup? Boolean True/False
ConfigRaspivoicePlaybackSpeed = Config.get('AfterSightConfigSettings','configraspivoiceplaybackspeed') #Playback rate of soundscapes
ConfigRaspivoiceCamera = Config.get('AfterSightConfigSettings','configraspivoicecamera') #Which image source to use? -s0 = image -s1 = rpi cam module -s2 = first usb cam -s3 = second usb cam etc.
ConfigJetpacNetwork = Config.get('AfterSightConfigSettings','configjetpacnetwork') #Which network to use
ConfigJetpacCamera = Config.get('AfterSightConfigSettings','configjetpaccamera') #which camera device to use Generate this from a list of /dev/videoX devices?
ConfigJetpacThreshold = Config.get('AfterSightConfigSettings','configjetpacthreshold') #Certainty threshold expressed as a two digit ratio (ie. 0.15)
ConfigVibrationStartup = Config.get('AfterSightConfigSettings','configvibrationstartup') #Is vibration enable on startup

#If you want to add a variable here, you must create an entry in aftersight.cfg as well. otherwise no bueno

bequiet = False #Key decision making variable. Shuts the main menuing system off while other processes that use the audio channel are in operation
                #Initially we want it to be loud and making decisions unless an application that uses audio launches on startup
if (ConfigRaspivoiceStartup == True and ConfigJetpacStartup == True): #Right now they both can't be true. When we fork the webcam to two virtual cams this will be possible
        ConfigRaspivoiceStartup = True
        ConfigJetpacStartup = False  #The temporary solution to this problem is to only startup raspivoice
if ConfigRaspivoiceStartup == True:
        bequiet = True #Prevents the menu items from being read or executed while external processes that use audio are running
        subprocess.Popen(["sudo","/home/pi/raspivoice/Release/./raspivoice","-A","--speak",ConfigRaspivoiceCamera,ConfigRaspivoicePlaybackSpeed]) #Launch if startup execution is the menu setting
if ConfigJetpacStartup == True:
        subprocess.Popen(["sudo","python","/home/pi/jetpac.py"])

vibration = False #By default vibration is turned off

if ConfigVibrationStartup == True: #If the config file sets rangefinder/vibration for startup, toggle the variable for the vibration motor
        vibration = True

print "Volume",ConfigVolume
print "Raspivoice on Startup?",ConfigRaspivoiceStartup
print "Jetpac on Startup?", ConfigJetpacStartup
print "Raspivoice Soundscape Playback Speed", ConfigRaspivoicePlaybackSpeed
print "Which Camera will raspivOICe use?" ,ConfigRaspivoiceCamera
print "Which Network will Jetpac Use?", ConfigJetpacNetwork
print "Which Camera will Jetpac Use?", ConfigJetpacCamera
print "What is the threshold value for Jetpac?", ConfigJetpacThreshold
print "Is Vibration Turned on at Startup?", ConfigVibrationStartup

#The print statements are just to confirm a good config read

A_Pin=4 #Encoder CC direction
B_Pin=5 #Enconder C direction
encoder = gaugette.rotary_encoder.RotaryEncoder.Worker(A_Pin, B_Pin)#Use worker class to try to catch transitions better.
encoder.start()#start the worker class encoder watcher
encoder.steps_per_cycle = 4 #the encoder always gives 4 for 1 detente

oldexternalpowerstate = 0 # this variable enables an espeak event when the power plug is inserted or removed

Main=["Launch Raspivoice","Launch Jetpac","Toggle Rangefinder Vibration","Settings","acknowledgements","Disclaimer"]
Settings=["Advance Volume","Raspivoice Settings", "Jetpac Settings","Return to main menu"]
RaspivoiceSettings = ["Toggle Playback Speed", "Next Camera", "Toggle Raspivoice Autostart", "Return to Main Menu"]
JetpacSettings = ["Next Network", "Next Threshold", "Next Camera", "Toggle Jetpac Autostart","Return to Main Menu"]
VolumeMenu = ["Volume Up", "Volume Down", "Return to Main Menu"]

#You can change and add menu items above, but you MUST go to the section where the MenuLevel and menupos are evaluated for a button press/release in under three seconds
#You have to change the actions for the items being evaluated there.
#If you don't, no bueno

MenuLevel = Main #Select the Main Menu first
menupos = 0 #position in menu list


seconddelta = 0

call (["sudo","espeak","MainMenu,Rotate,Knob,For,Options"])
while 1:  #Main Loop
    battstate = GPIO.input(27)
    switchstate = GPIO.input(9)
    externalpowerstate = GPIO.input(10)
    CurrentMenuMaxSize = len(MenuLevel)-1 #Have to subtract one because lists start at zero, but the len function returns only natural numbers

    delta = encoder.get_delta()

    if delta!=0:
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
        if seconddelta == 3: #This was the most important value to change to get reliable single increments of the menu items
                seconddelta = 0
                menupos=menupos+delta
                print "MenuPosition" ,menupos
                print MenuLevel
                print "Current Menu Max Size",CurrentMenuMaxSize
                if menupos > CurrentMenuMaxSize:
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
                #print ('External Power Connected')
                call (["sudo","espeak","ExternalPowerConnected"])
        elif (externalpowerstate ==0):
                #print ('External Power Disconnected')
                call (["sudo","espeak","ExternalPowerDisconnected"])
    if (externalpowerstate == 0):
        print ('External Power Disconnected, Running from Internal Battery')
    #if vibration == True:
        #print "Start Vibration Routines, or make sure they are already running"
    #elif (vibration == False):
        #print "End vibration routines, or make sure they are not running"
    if (switchstate == 1):
        #print ('Power Switch Turned Off, System Shutdown Initiated')
        call (["sudo", "espeak", "shutdown"])
        call (["sudo", "shutdown", "-h", "now"])
    #if (switchstate == 0):
        #print ('Power Switch Is On, Keep Working')
    #if (battstate == 1):
        #print ('Battery OK, keep system up')
    #if (battstate == 0):
        #print ('Battery Low, System Shutdown')
    if GPIO.input(25):
        #print('Button Released')
        if (t3 < 3 and t3 > 0): #If the button is released in under 3 seconds, execute the command for the currently selected menu and function
                print "Detected Button Release in less than 3 seconds"
                if bequiet == False:
                #Main=["Launch Raspivoice","Launch Jetpac","Toggle Rangefinder Vibration","Settings","acknowledgements","Disclaimer"]
                        if (MenuLevel == Main and menupos == 0): #1st option in main menu list is launch raspivoice
                                bequiet = True
                                subprocess.Popen(["sudo","/home/pi/raspivoice/Release/./raspivoice","-A","--speak",ConfigRaspivoiceCamera,ConfigRaspivoicePlaybackSpeed]) #Launch using config settings plus a few obligate command line flags for spoken menu and rotary encoder input
                        if (MenuLevel == Main and menupos == 1): #Second Option in main menu list is launch Jetpac
                                bequiet = True
                                subprocess.Popen(["sudo","python","/home/pi/jetpac.py"])
                        if (MenuLevel == Main and menupos == 2):
                                if vibration == True:
                                        call (["sudo","espeak","VibrationToggledOff"])
                                        call (["sudo","killall","rangefinder"])
                                        p.ChangeDutyCycle(0) #If it gets closed while active, this should quiet it down
                                        vibration = False
                                else:
                                        call (["sudo","espeak","VibrationToggledOn"])
                                        subprocess.Popen(["sudo","python","/home/pi/rangefinder.py"])
                                        vibration = True
                        if (MenuLevel == Main and menupos == 3): #Enter The Settings Menu
                                MenuLevel = Settings
                                call (["sudo","espeak","ChangeSettings"])
                                menupos = 10
                        if (MenuLevel == Main and menupos == 4):
                                espeak_process = subprocess.Popen(["espeak", "-f","/home/pi/acknowledgements.txt", "--stdout"], stdout=subprocess.PIPE)
                                subprocess.Popen(["aplay", "-D", "sysdefault"], stdin=espeak_process.stdout, stdout=subprocess.PIPE)
                        if (MenuLevel == Main and menupos == 5):
                                espeak_process = subprocess.Popen(["espeak", "-f","/home/pi/disclaimer.txt", "--stdout"], stdout=subprocess.PIPE)
                                subprocess.Popen(["aplay", "-D", "sysdefault"], stdin=espeak_process.stdout, stdout=subprocess.PIPE)
                #Settings=["Advance Volume","Raspivoice Settings", "Jetpac Settings","Return to main menu"]
                        if (MenuLevel == Settings and menupos == 0):
                                commandlinevolume = int(ConfigVolume)
                                commandlinevolume = commandlinevolume + 10
                                if commandlinevolume > 100: #Wrap volume back to lowest setting
                                        ConfigVolume = "70"
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
                                volumearg = ConfigVolume + "%"
                                call (["sudo","amixer","sset","PCM,0",volumearg])
                                ConfigVolume = str(commandlinevolume)
                                menupos = 0 #keep menu position on advance volume to allow for repeated presses
                        if (MenuLevel == Settings and menupos == 1):
                                MenuLevel = RaspivoiceSettings
                                call (["sudo","espeak","RaspivoiceSettings"])
                                menupos = 10
                        if (MenuLevel == Settings and menupos == 2):
                                MenuLevel = JetpacSettings
                                call (["sudo","espeak","JetpacSettings"])
                                menupos = 10
                        if (MenuLevel == Settings and menupos == 3):
                                MenuLevel = Main
                                call (["sudo","espeak","MainMenu"])
                                menupos = 10
                 #RaspivoiceSettings = ["Toggle Playback Speed", "Next Camera", "Toggle Raspivoice Autostart", "Return to Main Menu"]
                        if (MenuLevel == RaspivoiceSettings and menupos == 0):
                                if ConfigRaspivoicePlaybackSpeed  == "--total_time_s=1.05":
                                        call (["sudo","espeak","ChangedToFast"])
                                        ConfigRaspivoicePlaybackSpeed = "--total_time_s=0.5"
                                elif ConfigRaspivoicePlaybackSpeed == "--total_time_s=0.5":
                                        call (["sudo","espeak","ChangedToSlow"])
                                        ConfigRaspivoicePlaybackSpeed = "--total_time_s=2.0"
                                else:
                                        call (["sudo","espeak","ChangedToNormal"])
                                        ConfigRaspivoicePlaybackSpeed = "--total_time_s=1.05"
                                menupos = 0 #Keep at playback speed setting to allow repeated toggle
                        if (MenuLevel == RaspivoiceSettings and menupos == 1):
                                if ConfigRaspivoiceCamera == "-s2":
                                        call (["sudo","espeak","ChangedToCameraModule"])
                                        ConfigRaspivoiceCamera = "-s1"
                                else:
                                        call (["sudo","espeak","ChangedToUSBCamera1"])
                                        ConfigRaspivoiceCamera = "-s2"
                                menupos = 1 #Keep at camera advance point to allow repeated toggle
                        if (MenuLevel == RaspivoiceSettings and menupos == 2):
                                if ConfigRaspivoiceStartup == True:
                                        call (["sudo","espeak","NoLaunchOnStartup"])
                                        ConfigRaspivoiceStartup = False
                                else:
                                        call (["sudo","espeak","RaspivoiceWillAutostart"])
                                        ConfigRaspivoiceStartup = True
                        if (MenuLevel == RaspivoiceSettings and menupos == 3):
                                MenuLevel = Main
                                call (["sudo","espeak","Main Menu"])
                #JetpacSettings = ["Next Network", "Next Threshold", "Next Camera", "Toggle Jetpac Autostart","Return to Main Menu"]
                        if (MenuLevel == JetpacSettings and menupos == 0):
                                if ConfigJetpacNetwork == "/home/pi/projects/DeepBeliefSDK/networks/ccv2010.ntwk":
                                        call (["sudo","espeak","ChangingToLibCCV2012"])
                                        ConfigJetpacNetwork = "/home/pi/projects/DeepBeliefSDK/networks/ccv2012.ntwk" #Slow, Very Accurate = 2nd Best
                                elif ConfigJetpacNetwork == "/home/pi/projects/DeepBeliefSDK/networks/ccv2012.ntwk":
                                        call (["sudo","espeak","ChangingtoJetpacNetwork"])
                                        ConfigJetpacNetwork = "/home/pi/projects/DeepBeliefSDK/networks/jetpac.ntwk" #Fast, Fairly Accurate = Best
                                else:
                                        call (["sudo","espeak","ChangingToLibCCV2010"])
                                        ConfigJetpacNetwork = "/home/pi/projects/DeepBeliefSDK/networks/ccv2010.ntwk" #Slowest, Accurate =  3rd Best
                        if (MenuLevel == JetpacSettings and menupos == 1):
                                if ConfigJetpacThreshold == "0.05":
                                        call (["sudo","espeak","ChangingTo10%"]) #somewhat stringent
                                        ConfigJetpacThreshold = "0.10"
                                elif ConfigJetpacThreshold == "0.10":
                                        call (["sudo","espeak","ChangingTo15%"])
                                        ConfigJetpacThreshold = "0.15"            #More Stringent
                                elif ConfigJetpacThreshold == "0.15":
                                        call (["sudo","espeak","ChangingTo20%"])
                                        ConfigJetpacThreshold = "0.20"           #More Stringent
                                elif ConfigJetpacThreshold == "0.20":
                                        call (["sudo","espeak","ChangingTo25%"])
                                        ConfigJetpacThreshold = "0.25"
                                elif ConfigJetpacThreshold == "0.25":
                                        call (["sudo","espeak","Changingto30%"])
                                        ConfigJetpacThreshold = "0.30"            #Most stringent
                                else:
                                        call (["sudo","espeak","ChangingTo5%"])
                                        ConfigJetpacThreshold = "0.05"            #Mid Stringency
                        if (MenuLevel == JetpacSettings and menupos == 2):
                                if ConfigJetpacCamera == "/dev/video0":
                                        call (["sudo","espeak","ChangingToUSBCamera1"])
                                        ConfigJetpacCamera = "/dev/video1"
                                else:
                                        call (["sudo","espeak","ChangingToUSBCamera0"])
                                        ConfigJetpacCamera = "/dev/video0"
                        if (MenuLevel == JetpacSettings and menupos == 3):
                                if ConfigJetpacStartup == True:
                                        call (["sudo","espeak","NoLaunchOnStartup"])
                                        ConfigJetpacStartup = False
                                else:
                                        call (["sudo","espeak","JetpacWillAutostart"])
                                        ConfigJetpacStartup = True
                        if (MenuLevel == JetpacSettings and menupos == 4):
                                MenuLevel = Main
                                call (["sudo","espeak","Main Menu"])
                                menupos = 10
                        #Are the changes being reflected in the variables we want to write?
                        print "Volume",ConfigVolume
                        print "Raspivoice on Startup?",ConfigRaspivoiceStartup
                        print "Jetpac on Startup?", ConfigJetpacStartup
                        print "Raspivoice Soundscape Playback Speed", ConfigRaspivoicePlaybackSpeed
                        print "Which Camera will raspivOICe use?" ,ConfigRaspivoiceCamera
                        print "Which Network will Jetpac Use?", ConfigJetpacNetwork
                        print "Which Camera will Jetpac Use?", ConfigJetpacCamera
                        print "What is the threshold value for Jetpac?", ConfigJetpacThreshold
                        print "Is Vibration Turned on at Startup?", ConfigVibrationStartup
                        #Now lets set configparser up to write to file
                        Config.set('AfterSightConfigSettings','configvolume',ConfigVolume)
                        Config.set('AfterSightConfigSettings','configraspivoicestartup',ConfigRaspivoiceStartup)
                        Config.set('AfterSightConfigSettings','configjetpacstartup',ConfigJetpacStartup)
                        Config.set('AfterSightConfigSettings','configraspivoiceplaybackspeed',ConfigRaspivoicePlaybackSpeed)
                        Config.set('AfterSightConfigSettings','configraspivoicecamera',ConfigRaspivoiceCamera)
                        Config.set('AfterSightConfigSettings','configjetpacnetwork',ConfigJetpacNetwork)
                        Config.set('AfterSightConfigSettings','configjetpaccamera',ConfigJetpacCamera)
                        Config.set('AfterSightConfigSettings','configjetpacthreshold',ConfigJetpacThreshold)
                        Config.set('AfterSightConfigSettings','configvibrationstartup',ConfigVibrationStartup)
                        with open('aftersight.cfg', 'w') as configfile:    # save
                                Config.write(configfile)

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
        call (["sudo","killall","espeak"])
        call (["sudo","espeak","Terminating Programs"])
        call (["sudo","killall","raspivoice"]) # Kills raspivoice if its running
        call (["sudo","killall","jpcnn"]) #Kills jetpac neural net process
        call (["sudo","killall","jetpac"]) #Kills Jetpac Python Looper
        call (["sudo","killall","rangefinder"]) #Kills rangefinder vibration motor python looper
        p.ChangeDutyCycle(0) #If the vibration motor was interrupted in an energetic config this should quiet it
        bequiet = False
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