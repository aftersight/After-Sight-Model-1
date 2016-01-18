#pragma once

#include "AudioData.h"
#include <string>

//2D indexing: column-major order, 0-based:
#define IDX2D(row, column) (((column) * rows) + (row))


class ImageToSoundscapeConverter
{
private:
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

	int rows;
	int columns;

	const uint32_t sampleCount;
	const uint32_t samplesPerColumn;
	const float timePerSample_s;
	const float scale;

	std::vector<float> omega;
	std::vector<float> phi0;
	std::vector<float> waveformCacheLeftChannel;
	std::vector<float> waveformCacheRightChannel;

	AudioData audioData;

	float rnd(void);

	void initWaveformCacheStereo();
	void processMono(const std::vector<float> &image);
	void processStereo(const std::vector<float> &image);
public:

	ImageToSoundscapeConverter(int rows, int columns, double freq_lowest = 500, double freq_highest = 5000,
							   int sample_freq_Hz = 44100, double total_time_s = 1.05, bool use_exponential = true,
							   bool use_stereo = true, bool use_delay = true, bool use_fade = true,
							   bool use_diffraction = true, bool use_bspline = true, float speed_of_sound_m_s = 340,
							   float acoustical_size_of_head_m = 0.20);

	void Process(const std::vector<float> &image);
	AudioData& GetAudioData() { return audioData; }
};

