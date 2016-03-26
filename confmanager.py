import ConfigParser # Lets us user aftersight.cfg easily
class ConfManager:
        def __init__(self):
                #Use ConfigParser to Read Persistent Variables from AfterSight.CFG

                self.Config = ConfigParser.RawConfigParser() #set variable to read config into
                self.Config.read('aftersight.cfg') #read from aftersight.cfg
                self.ConfigVolume = self.Config.get('AfterSightConfigSettings','configvolume') #volume setting percentage
                self.ConfigRaspivoiceStartup = self.Config.getboolean('AfterSightConfigSettings','configraspivoicestartup') #Does raspivoice execute on startup? Boolean True/False
                self.ConfigTeradeepStartup = self.Config.getboolean('AfterSightConfigSettings','configteradeepstartup') #Does Teradeep execute on startup? Boolean True/False
                self.ConfigRaspivoicePlaybackSpeed = self.Config.get('AfterSightConfigSettings','configraspivoiceplaybackspeed') #Playback rate of soundscapes
                self.ConfigRaspivoiceCamera = self.Config.get('AfterSightConfigSettings','configraspivoicecamera') #Which image source to use? -s0 = image -s1 = rpi cam module -s2 = first usb cam -s3 = second usb cam etc.
                self.ConfigTeradeepThreshold = self.Config.get('AfterSightConfigSettings','configteradeepthreshold') #Certainty threshold expressed as a two digit ratio (ie. 15)
                self.ConfigVibrationStartup = self.Config.getboolean('AfterSightConfigSettings','configvibrationstartup') #Is vibration enable on startup
                self.ConfigAudibleDistance = self.Config.getboolean('AfterSightConfigSettings','configaudibledistance') #Read the distance on the audio channel?
                self.ConfigBlinders = self.Config.get('AfterSightConfigSettings','configblinders') #Are blinders enabled?
                self.ConfigZoom = self.Config.get('AfterSightConfigSettings','configzoom')#What zoom level is selected? 0, 150%, 200% (0,1.5,2.0)
                self.ConfigFovealmapping = self.Config.get('AfterSightConfigSettings','configfovealmapping') #Is foveal mapping enabled?
		self.ConfigVibrationEnabled = self.Config.get('AfterSightConfigSettings','configvibrationenabled') #Enable vibration motor
		self.ConfigVibrateSoundEnabled = self.Config.get('AfterSightConfigSettings','configvibratesoundenabled') #Is the sound version of the vibration enabled?
                self.ConfigUpdateNumber = self.Config.get('AfterSightConfigSettings','configupdatenumber') #What is the current update number.  This will be user to pick which update $
                self.ConfigBatteryShutdown = self.Config.getboolean('AfterSightConfigSettings','configbatteryshutdown')#Is the timed battery shutdown enabled?

		#If you want to add a variable here, you must create an entry in aftersight.cfg as well. otherwise no bueno

        def save(self):
                #Are the changes being reflected in the variables we want to write?
                #Now lets set configparser up to write to file
                self.Config.set('AfterSightConfigSettings','configvolume',self.ConfigVolume)
                self.Config.set('AfterSightConfigSettings','configraspivoicestartup',self.ConfigRaspivoiceStartup)
                self.Config.set('AfterSightConfigSettings','configteradeepstartup',self.ConfigTeradeepStartup)
                self.Config.set('AfterSightConfigSettings','configraspivoiceplaybackspeed',self.ConfigRaspivoicePlaybackSpeed)
                self.Config.set('AfterSightConfigSettings','configraspivoicecamera',self.ConfigRaspivoiceCamera)
                self.Config.set('AfterSightConfigSettings','configteradeepthreshold',self.ConfigTeradeepThreshold)
                self.Config.set('AfterSightConfigSettings','configvibrationstartup',self.ConfigVibrationStartup)
                self.Config.set('AfterSightConfigSettings','configaudibledistance',self.ConfigAudibleDistance)
                self.Config.set('AfterSightConfigSettings','configblinders',self.ConfigBlinders)
                self.Config.set('AfterSightConfigSettings','configzoom',self.ConfigZoom)
                self.Config.set('AfterSightConfigSettings','configfovealmapping',self.ConfigFovealmapping)
		self.Config.set('AfterSightConfigSettings','configvibrationenabled', self.ConfigVibrationEnabled)
		self.Config.set('AfterSightConfigSettings','configvibratesoundenabled', self.ConfigVibrateSoundEnabled)
		self.Config.set('AfterSightConfigSettings','configupdatenumber',self.ConfigUpdateNumber)
		self.Config.set('AfterSightConfigSettings','configbatteryshudown',self.ConfigBatteryShutdown)
		with open('aftersight.cfg', 'w') as configfile:    # save
                        self.Config.write(configfile)
