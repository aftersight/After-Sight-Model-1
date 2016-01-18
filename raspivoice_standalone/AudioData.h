#pragma once

#include <vector>
#include <string>
#include <cstdio>
#include <cinttypes>

class AudioData
{
private:
	const bool use_stereo;
	const int sample_freq_Hz;
	const int sample_count;
	std::vector<uint16_t> samplebuffer;
	static pthread_mutex_t audio_mutex;
	int volume;
	int newvolume;

	void wi(FILE* fp, uint16_t i);
	void wl(FILE* fp, uint32_t l);
	int updateVolume();
public:
	int CardNumber;
	bool Verbose;

	static void Init();
	AudioData(int card_number, int sample_freq_Hz = 48000, int sample_count = 0, bool use_stereo = true);
	
	uint16_t *Data() { return &samplebuffer[0]; };

	void SaveToWavFile(std::string filename);
	
	void Play();
	int PlayWav(std::string filename);
	void SetVolume(int newvolume);
	bool Speak(std::string text);
};

