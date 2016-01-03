#pragma once

#include <getopt.h>
#include <string>

typedef struct
{
	int rows;
	int columns;
	int image_source;
	std::string input_filename;
	std::string output_filename;
	int audio_card;
	int volume;
	bool preview;
	bool use_bw_test_image;
	bool verbose;
	bool negative_image;
	int flip;
	int read_frames;
	int exposure;
	int brightness;
	float contrast;
	int blinders;
	float zoom;
	bool foveal_mapping;
	int threshold;
	float edge_detection_opacity;
	int edge_detection_threshold;
	double freq_lowest;
	double freq_highest;
	int	sample_freq_Hz;
	double total_time_s;
	bool use_exponential;
	bool use_stereo;
	bool use_delay;
	bool use_fade;
	bool use_diffraction;
	bool use_bspline;
	float speed_of_sound_m_s;
	float acoustical_size_of_head_m;
	bool mute;
	bool daemon;
	std::string grab_keyboard;
	bool use_rotary_encoder;
	bool speak;

	bool quit;
} RaspiVoiceOptions;

extern RaspiVoiceOptions rvopt;
extern pthread_mutex_t rvopt_mutex;

RaspiVoiceOptions GetDefaultOptions(void);
bool SetCommandLineOptions(int argc, char *argv[]);
RaspiVoiceOptions GetCommandLineOptions();
void ShowHelp(void);
