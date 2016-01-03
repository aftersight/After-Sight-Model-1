#include <string>
#include <iostream>
#include <cstdlib>

#include "Options.h"

RaspiVoiceOptions cmdLineOptions;

RaspiVoiceOptions rvopt;
pthread_mutex_t rvopt_mutex;

static struct option long_getopt_options[] =
{
	{ "help", no_argument, 0, 'h' },
	{ "daemon", no_argument, 0, 'd' },
	{ "rows", required_argument, 0, 'r' },
	{ "columns", required_argument, 0, 'c' },
	{ "image_source", required_argument, 0, 's' },
	{ "input_filename", required_argument, 0, 'i' },
	{ "output_filename", required_argument, 0, 'o' },
	{ "audio_card", required_argument, 0, 'a' },
	{ "volume", required_argument, 0, 'V' },
	{ "preview", no_argument, 0, 'p' },
	{ "use_bw_test_image", required_argument, 0, 'I' },
	{ "verbose", no_argument, 0, 'v' },
	{ "negative_image", no_argument, 0, 'n' },
	{ "flip", required_argument, 0, 'f' },
	{ "read_frames", required_argument, 0, 'R' },
	{ "exposure", required_argument, 0, 'e' },
	{ "brightness", required_argument, 0, 'B' },
	{ "contrast", required_argument, 0, 'C' },
	{ "blinders", required_argument, 0, 'b' },
	{ "zoom", required_argument, 0, 'z' },
	{ "foveal_mapping", no_argument, 0, 'm' },
	{ "edge_detection_opacity", required_argument, 0, 'E' },
	{ "edge_detection_threshold", required_argument, 0, 'G' },
	{ "freq_lowest", required_argument, 0, 'L' },
	{ "freq_highest", required_argument, 0, 'H' },
	{ "total_time_s", required_argument, 0, 't' },
	{ "use_exponential", required_argument, 0, 'x' },
	{ "use_delay", required_argument, 0, 'y' },
	{ "use_fade", required_argument, 0, 'F' },
	{ "use_diffraction", required_argument, 0, 'D' },
	{ "use_bspline", required_argument, 0, 'N' },
	{ "sample_freq_Hz", required_argument, 0, 'Z' },
	{ "threshold", required_argument, 0, 'T' },
	{ "use_stereo", required_argument, 0, 'O' },
	{ "grab_keyboard", required_argument, 0, 'g' },
	{ "use_rotary_encoder", no_argument, 0, 'A' },
	{ "speak", no_argument, 0, 'S' },
	{ 0, 0, 0, 0 }
}; 

RaspiVoiceOptions GetDefaultOptions()
{
	RaspiVoiceOptions opt;

	opt.rows = 64;
	opt.columns = 176;
	opt.image_source = 1;
	opt.input_filename = "";
	opt.output_filename = "";
	opt.audio_card = 0;
	opt.volume = -1;
	opt.preview = false;
	opt.use_bw_test_image = false;
	opt.verbose = false;
	opt.negative_image = false;
	opt.flip = 0;
	opt.read_frames = 2;
	opt.exposure = 0;
	opt.brightness = 0;
	opt.contrast = 1.0;
	opt.blinders = 0;
	opt.zoom = 1;
	opt.foveal_mapping = false;
	opt.threshold = 0;
	opt.edge_detection_opacity = 0.0;
	opt.edge_detection_threshold = 50;
	opt.freq_lowest = 500;
	opt.freq_highest = 5000;
	opt.sample_freq_Hz = 48000;
	opt.total_time_s = 1.05;
	opt.use_exponential = true;
	opt.use_stereo = true;
	opt.use_delay = true;
	opt.use_fade = true;
	opt.use_diffraction = true;
	opt.use_bspline = true;
	opt.speed_of_sound_m_s = 340;
	opt.acoustical_size_of_head_m = 0.20;
	opt.mute = false;
	opt.daemon = false;
	opt.grab_keyboard = "";
	opt.use_rotary_encoder = false;
	opt.speak = false;

	opt.quit = false;

	return opt;
}


//Returns false if program should be aborted, true otherwise.
bool SetCommandLineOptions(int argc, char *argv[])
{
	RaspiVoiceOptions opt = GetDefaultOptions();

	//Retrieve command line options:
	int option_index = 0;
	int cmdline_opt;
	while ((cmdline_opt = getopt_long_only(argc, argv, "hdr:c:s:i:o:a:V:pI:vnf:R:e:B:C:b:z:mE:G:L:H:t:x:y:d:F:D:N:Z:T:O:g:AS", long_getopt_options, &option_index)) != -1)
	{
		switch (cmdline_opt)
		{
			case 0:
				break;
			case 'h':
				ShowHelp();
				return false;
			case 'd':
				opt.daemon = true;
				break;
			case 'r':
				opt.rows = atoi(optarg);
				break;
			case 'c':
				opt.columns = atoi(optarg);
				break;
			case 's':
				opt.image_source = atoi(optarg);
				break;
			case 'i':
				opt.input_filename = optarg;
				break;
			case 'o':
				opt.output_filename = optarg;
				break;
			case 'a':
				opt.audio_card = atoi(optarg);
				break;
			case 'V':
				opt.volume = atoi(optarg);
				break;
			case 'p':
				opt.preview = true;
				break;
			case 'I':
				opt.use_bw_test_image = (atoi(optarg) != 0);
				break;
			case 'v':
				opt.verbose = true;
				break;
			case 'f':
				opt.flip = atoi(optarg);
				break;
			case 'n':
				opt.negative_image = true;
				break;
			case 'E':
				opt.edge_detection_opacity = atof(optarg);
				break;
			case 'G':
				opt.edge_detection_threshold = atoi(optarg);
				break;
			case 'L':
				opt.freq_lowest = atof(optarg);
				break;
			case 'H':
				opt.freq_highest = atof(optarg);
				break;
			case 't':
				opt.total_time_s = atof(optarg);
				break;
			case 'x':
				opt.use_exponential = (atoi(optarg) != 0);
				break;
			case 'y':
				opt.use_delay = (atoi(optarg) != 0);
				break;
			case 'F':
				opt.use_fade = (atoi(optarg) != 0);
				break;
			case 'R':
				opt.read_frames = atoi(optarg);
				break;
			case 'e':
				opt.exposure = atoi(optarg);
				break;
			case 'B':
				opt.brightness = atoi(optarg);
				break;
			case 'C':
				opt.contrast = atof(optarg);
				break;
			case 'b':
				opt.blinders = atoi(optarg);
				break;
			case 'z':
				opt.zoom = atof(optarg);
				break;
			case 'm':
				opt.foveal_mapping = true;
				break;
			case 'D':
				opt.use_diffraction = (atoi(optarg) != 0);
				break;
			case 'N':
				opt.use_bspline = (atoi(optarg) != 0);
				break;
			case 'Z':
				opt.sample_freq_Hz = atof(optarg);
				break;
			case 'T':
				opt.threshold = atoi(optarg);
				break;
			case 'O':
				opt.use_stereo = (atoi(optarg) != 0);
				break;
			case 'g':
				opt.grab_keyboard = optarg;
				break;
			case 'A':
				opt.use_rotary_encoder = true;
				break;
			case 'S':
				opt.speak = true;
				break;
			default:
				std::cout << "Type raspivoice --help for available options." << std::endl;
				return false;
		}
	}

	if (optind < argc)
	{
		std::cerr << "Invalid argument: " << argv[optind] << std::endl;
		std::cerr << "Type raspivoice --help for available options." << std::endl;
		return false;
	}

	cmdLineOptions = opt;

	return true;
}


RaspiVoiceOptions GetCommandLineOptions()
{
	return cmdLineOptions;
}


void ShowHelp()
{
	std::cout << "Usage: " << std::endl;
	std::cout << "raspivoice {options}" << std::endl;
	std::cout << std::endl;
	std::cout << "Options [defaults]: " << std::endl;
	std::cout << "-h, --help\t\t\t\tThis help text" << std::endl;
	std::cout << "-d  --daemon\t\t\t\tDaemon mode (run in background)" << std::endl;
	std::cout << "-r, --rows=[64]\t\t\t\tNumber of rows, i.e. vertical (frequency) soundscape resolution (ignored if test image is used)" << std::endl;
	std::cout << "-c, --columns=[178]\t\t\tNumber of columns, i.e. horizontal (time) soundscape resolution (ignored if test image is used)" << std::endl;
	std::cout << "-s, --image_source=[1]\t\t\tImage source: 0 for image file, 1 for RaspiCam, 2 for 1st USB camera, 3 for 2nd USB camera..." << std::endl;
	std::cout << "-i, --input_filename=[]\t\t\tPath to image file (bmp,jpg,png,ppm,tif). Reread every frame. Static test image is used if empty." << std::endl;
	std::cout << "-o, --output_filename=[]\t\tPath to output file (wav). Written every frame if not muted." << std::endl;
	std::cout << "-a, --audio_card=[0]\t\t\tAudio card number (0,1,...), use aplay -l to get list" << std::endl;
	std::cout << "-V, --volume=[-1]\t\t\tAudio volume (set by system mixer, 0-100, -1 for no change)" << std::endl;
	std::cout << "-S, --speak\t\t\t\tSpeak out option changes (espeak)." << std::endl;
	std::cout << "-g  --grab_keyboard=[]\t\t\tGrab keyboard device for exclusive access. Use device number(s) 0,1,2... (comma separated without spaces) from /dev/input/event*" << std::endl;
	std::cout << "-A  --use_rotary_encoder\t\tUse rotary encoder on GPIO" << std::endl;
	std::cout << "-p, --preview\t\t\t\tOpen preview window(s). X server required." << std::endl;
	std::cout << "-v, --verbose\t\t\t\tVerbose outputs." << std::endl;
	std::cout << "-n, --negative_image\t\t\tSwap bright and dark." << std::endl;
	std::cout << "-f, --flip=[0]\t\t\t\t0: no flipping, 1: horizontal, 2: verticel, 3: both" << std::endl;
	std::cout << "-R, --read_frames=[2]\t\t\tSet number of frames to read from camera before processing (>= 1). Optimize for minimal lag." << std::endl;
	std::cout << "-e  --exposure=[0]\t\t\tCamera exposure time setting, 1-100. Use 0 for auto." << std::endl;
	std::cout << "-B  --brightness=[0]\t\t\tAdditional brightness, -255 to 255." << std::endl;
	std::cout << "-C  --contrast=[1.0]\t\t\tContrast enhancement factor >= 1.0" << std::endl;
	std::cout << "-b  --blinders=[0]\t\t\tBlinders left and right, pixel size (0-89 for default columns)" << std::endl;
	std::cout << "-z  --zoom=[1.0]\t\t\tZoom factor (>= 1.0)" << std::endl;
	std::cout << "-m  --foveal_mapping\t\t\tEnable foveal mapping (barrel distortion magnifying center region)" << std::endl;
	std::cout << "-T, --threshold=[0]\t\t\tEnable threshold for black/white image if > 0. Range 1-255, use 127 as a starting point. 255=auto." << std::endl;
	std::cout << "-E, --edge_detection_opacity=[0.0]\tEnable edge detection if > 0. Opacity of detected edges between 0.0 and 1.0." << std::endl;
	std::cout << "-G  --edge_detection_threshold=[50]\tEdge detection threshold value 1-255." << std::endl;
	std::cout << "-L, --freq_lowest=[500]" << std::endl;
	std::cout << "-H, --freq_highest=[5000]" << std::endl;
	std::cout << "-t, --total_time_s=[1.05]" << std::endl;
	std::cout << "-x  --use_exponential=[1]" << std::endl;
	//std::cout << "-o  --use_stereo=[1]" << std::endl;
	std::cout << "-d, --use_delay=[1]" << std::endl;
	std::cout << "-F, --use_fade=[1]" << std::endl;
	std::cout << "-D  --use_diffraction=[1]" << std::endl;
	std::cout << "-N  --use_bspline=[1]" << std::endl;
	std::cout << "-Z  --sample_freq_Hz=[48000]" << std::endl;
	std::cout << std::endl;
}