// raspivoice
// Based on:
// http://www.seeingwithsound.com/hificode_OpenCV.cpp
// C program for soundscape generation. (C) P.B.L. Meijer 1996
// hificode.c modified for camera input using OpenCV. (C) 2013
// Last update: December 29, 2014; released under the Creative
// Commons Attribution 4.0 International License (CC BY 4.0),
// see http://www.seeingwithsound.com/im2sound.htm for details
// License: https://creativecommons.org/licenses/by/4.0/

#include <cstring>
#include <stdexcept>
#include <iostream>
#include <sstream>

#include "AudioData.h"

pthread_mutex_t AudioData::audio_mutex;

AudioData::AudioData(int card_number, int sample_freq_Hz, int sample_count, bool use_stereo) :
	sample_freq_Hz(sample_freq_Hz),
	sample_count(sample_count),
	use_stereo(use_stereo),
	Verbose(false),
	CardNumber(card_number),
	samplebuffer(std::vector<uint16_t>((use_stereo ? 2 : 1) * sample_count)),
	volume(-1),
	newvolume(-1)
{
}

void AudioData::Init()
{
	pthread_mutex_init(&audio_mutex, NULL);
}

void AudioData::wi(FILE* fp, uint16_t i)
{
	int b1, b0;
	b0 = i % 256;
	b1 = (i - b0) / 256;
	putc(b0, fp);
	putc(b1, fp);
}

void AudioData::wl(FILE* fp, uint32_t l)
{
	unsigned int i1, i0;
	i0 = l % 65536L;
	i1 = (l - i0) / 65536L;
	wi(fp, i0);
	wi(fp, i1);
}

void AudioData::SaveToWavFile(std::string filename)
{
	FILE *fp;
	int bytes_per_sample = (use_stereo ? 4 : 2);

	// Write 8/16-bit mono/stereo .wav file
	fp = fopen(filename.c_str(), "wb");
	fprintf(fp, "RIFF");
	wl(fp, sample_count * bytes_per_sample + 36L);
	fprintf(fp, "WAVEfmt ");
	wl(fp, 16L);
	wi(fp, 1);
	wi(fp, use_stereo ? 2 : 1);
	wl(fp, 0L + sample_freq_Hz);
	wl(fp, 0L + sample_freq_Hz * bytes_per_sample);
	wi(fp, bytes_per_sample);
	wi(fp, 16);
	fprintf(fp, "data");
	wl(fp, sample_count * bytes_per_sample);

	fwrite(samplebuffer.data(), bytes_per_sample, sample_count, fp);
	fclose(fp);
}

void AudioData::Play()
{
	updateVolume();
	
	int bytes_per_sample = (use_stereo ? 4 : 2);

	std::stringstream cmd;
	cmd << "aplay --nonblock -r" << sample_freq_Hz << " -c" << (use_stereo ? 2 : 1) << " -fS16_LE -D plughw:" << CardNumber;
	if (!Verbose)
	{
		cmd << " -q";
	}
	else
	{
		std::cout << cmd.str() << std::endl;
	}

	pthread_mutex_lock(&audio_mutex);
	FILE* p = popen(cmd.str().c_str(), "w");
	fwrite(samplebuffer.data(), bytes_per_sample, sample_count, p);
	pclose(p);
	pthread_mutex_unlock(&audio_mutex);
}

int AudioData::PlayWav(std::string filename)
{
	char command[256] = "";
	int status;
	snprintf(command, 256, "aplay %s -D hw:%d", filename.c_str(), CardNumber);
	pthread_mutex_lock(&audio_mutex);
	status = system(command);
	pthread_mutex_unlock(&audio_mutex);
	return status;
}

void AudioData::SetVolume(int newvolume)
{
	this->newvolume = newvolume;
}

int AudioData::updateVolume()
{
	if ((volume == newvolume) || (newvolume == -1))
	{
		return 0;
	}

	volume = newvolume;

	char command[256] = "";
	int status = 0;
	snprintf(command, 256, "amixer -c %d controls | grep MIXER | grep Playback | grep Volume | sed s/[^0-9]*//g", CardNumber);
	//std::cout << command << std::endl;

	pthread_mutex_lock(&audio_mutex);
	FILE *fp = popen(command, "r");
	if (fp == nullptr)
	{
		return -1;
	}
	char buffer[256];
	char *res;
	while (!feof(fp) && status == 0)
		{
		res = fgets(buffer, sizeof(buffer), fp);
		if ((res == nullptr) || atoi(res) == 0)
		{
			status = -1;
		}
		else
		{
			int numid = atoi(res);
			snprintf(command, sizeof(command), "amixer -c %d cset numid=%d %d%% -q", CardNumber, numid, newvolume);
			//std::cout << command << std::endl;

			status = system(command);
		}
	}
	pclose(fp);
	pthread_mutex_unlock(&audio_mutex);
	return status;
}

bool AudioData::Speak(std::string text)
{
	updateVolume();

	char command[1023] = "";
	int status;
	snprintf(command, 1023, "espeak --stdout \"%s\" | aplay -q -D plughw:%d", text.c_str(), CardNumber);
	pthread_mutex_lock(&audio_mutex);
	int res = system(command);
	pthread_mutex_unlock(&audio_mutex);
	return (res == 0);
}
