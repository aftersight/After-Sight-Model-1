// raspivoice
// Based on:
// http://www.seeingwithsound.com/hificode_OpenCV.cpp
// C program for soundscape generation. (C) P.B.L. Meijer 1996
// hificode.c modified for camera input using OpenCV. (C) 2013
// Last update: December 29, 2014; released under the Creative
// Commons Attribution 4.0 International License (CC BY 4.0),
// see http://www.seeingwithsound.com/im2sound.htm for details
// License: https://creativecommons.org/licenses/by/4.0/

#include <cstdlib>
#include <cinttypes>
#include <cmath>
#include <stdexcept>

#include "ImageToSoundscape.h"

#define TwoPi 6.283185307179586476925287

ImageToSoundscapeConverter::ImageToSoundscapeConverter(int rows, int columns, double freq_lowest, double freq_highest,
													   int sample_freq_Hz, double total_time_s, bool use_exponential,
													   bool use_stereo, bool use_delay, bool use_fade,
													   bool use_diffraction, bool use_bspline, float speed_of_sound_m_s,
													   float acoustical_size_of_head_m) :
	rows(rows),
	columns(columns), freq_lowest(freq_lowest),
	freq_highest(freq_highest),
	sample_freq_Hz(sample_freq_Hz),
	total_time_s(total_time_s),
	use_exponential(use_exponential),
	use_stereo(use_stereo),
	use_delay(use_delay),
	use_fade(use_fade),
	use_diffraction(use_diffraction),
	use_bspline(use_bspline),
	speed_of_sound_m_s(speed_of_sound_m_s),
	acoustical_size_of_head_m(acoustical_size_of_head_m),

	sampleCount(2L * (uint32_t)(0.5 * sample_freq_Hz * total_time_s)),
	samplesPerColumn((uint32_t)(sampleCount / columns)),
	timePerSample_s(1.0 / sample_freq_Hz),
	scale(0.5 / sqrt((float)rows)),
	audioData(0, sample_freq_Hz, sampleCount, use_stereo),
	omega(std::vector<float>(rows)),
	phi0(std::vector<float>(rows)),
	waveformCacheLeftChannel(std::vector<float>(sampleCount*rows)),
	waveformCacheRightChannel(std::vector<float>(sampleCount*rows))
{
	// Set lin|exp (0|1) frequency distribution and random initial phase
	if (use_exponential)
	{
		for (int i = 0; i < rows; i++)
		{
			omega[i] = TwoPi * freq_lowest * pow(1.0 * freq_highest / freq_lowest, 1.0 * i / (rows - 1));
		}
	}
	else
	{
		for (int i = 0; i < rows; i++)
		{
			omega[i] = TwoPi * freq_lowest + TwoPi * (freq_highest - freq_lowest) * i / (rows - 1);
		}
	}

	for (int i = 0; i<rows; i++)
	{
		phi0[i] = TwoPi * rnd();
	}

	initWaveformCacheStereo();
}

float ImageToSoundscapeConverter::rnd()
{
	static uint32_t ir = 0L;
	uint32_t ia = 9301, ic = 49297, im = 233280;
	ir = (ir*ia + ic) % im;
	return ir / (1.0 * im);
}


void ImageToSoundscapeConverter::Process(const std::vector<float> &image)
{
	if (!use_stereo)
	{
		processMono(image);
	}
	else
	{
		processStereo(image);
	}
}


void ImageToSoundscapeConverter::processMono(const std::vector<float> &image)
{
	throw std::runtime_error("Mono audio not implemented");
	/*
	float tau1 = 0.5 / omega[rows - 1];
	float tau2 = 0.25 * tau1*tau1;
	float y = yl = yr = z = zl = zr = 0.0;

	while (int sample < sampleCount)
	{
		if (use_bspline)
		{
			q = 1.0 * (sample%samplesPerColumn) / (samplesPerColumn - 1);
			q2 = 0.5*q*q;
		}
		j = sample / samplesPerColumn;
		if (j > columns - 1)
		{
			j = columns - 1;
		}
		float s = 0.0;
		t = sample * timePerSample_s;
		if (sample < sample_count / (5 * columns))
		{
			s = (2.0*rnd() - 1.0) / scale; // "click"
		}
		else
		{
			for (int i = 0; i < rows; i++)
			{
				float a;
				if (use_bspline)
				{
					// Quadratic B-spline for smooth C1 time window
					if (j == 0)
					{
						a = (1.0 - q2)*image[j][i] + q2*image[j+1][i];
					}
					else if (j == columns - 1)
					{
						a = (q2 - q + 0.5)*image[j-1][i] + (0.5 + q - q2)*image[j][i];
					}
					else
					{
						a = (q2 - q + 0.5)*image[j-1][i] + (0.5 + q - q*q)*image[j][i] + q2*image[j+1][i];
					}
				}
				else
				{
					a = image[j][i];   // Rectangular time window
				}
				s += a * sin(omega[i] * t + phi0[i]);
			}
		}
		yp = y;
		y = tau1 / timePerSample_s + tau2 / (timePerSample_s*timePerSample_s);
		y = (s + y * yp + tau2 / timePerSample_s * z) / (1.0 + y);
		z = (y - yp) / timePerSample_s;
		l = sso + 0.5 + scale * ssm * y; // y = 2nd order filtered s
		if (l >= sso - 1 + ssm)
		{
			l = sso - 1 + ssm;
		}
		if (l < sso - ssm)
		{
			l = sso - ssm;
		}
		ss = (unsigned int)l;
		wi(ss);
		sample++;
	}
	*/
}




void ImageToSoundscapeConverter::processStereo(const std::vector<float> &image)
{
	float tau1 = 0.5 / omega[rows - 1];
	float tau2 = 0.25 * tau1*tau1;
	float yl = 0.0, yr = 0.0;
	float zl = 0.0, zr = 0.0;
	for (int sample = 0; sample < sampleCount; sample++)
	{
		float q, q2, f1, f2;
		if (use_bspline)
		{
			q = 1.0 * (sample % samplesPerColumn) / (samplesPerColumn - 1);
			q2 = 0.5 * q * q;
			f1 = (q2 - q + 0.5);
			f2 = (0.5 + q - q*q);
		}

		int j = sample / samplesPerColumn;
		if (j > columns - 1)
		{
			j = columns - 1;
		}

		float r = 1.0 * sample / (sampleCount - 1);  // Binaural attenuation/delay parameter
		float theta = (r - 0.5) * TwoPi / 3;
		float x = 0.5 * acoustical_size_of_head_m * (theta + sin(theta));
		float tl = sample * timePerSample_s;
		float tr = tl;
		if (use_delay)
		{
			tr += x / speed_of_sound_m_s;  // Time delay model
		}
		x = fabs(x);
		float sl = 0.0, sr = 0.0;

		const float *im1, *im2, *im3;
		if (j > 0)
		{
			im1 = &image[IDX2D(0, j - 1)];
		}
		im2 = &image[IDX2D(0, j)];
		if (j < columns - 1)
		{
			im3 = &image[IDX2D(0, j + 1)];
		}

		for (int i = 0; i < rows; i++)
		{
			float a;
			if (use_bspline)
			{
				if (j == 0)
				{
					a = (1.0 - q2)*im2[i] + q2*im3[i];
				}
				else if (j == columns - 1)
				{
					a = f1*im1[i] + f2*im2[i];
				}
				else
				{
					a = f1*im1[i] + f2*im2[i] + q2*im3[i];
				}
			}
			else
			{
				a = im2[i];
			}

			sl += a * waveformCacheLeftChannel[(sample * rows) + i];
			sr += a * waveformCacheRightChannel[(sample * rows) + i];
		}

		if (sample < sampleCount / (5 * columns))
		{
			sl = (2.0*rnd() - 1.0) / scale;   // Left "click"
		}

		if (tl < 0.0)
		{
			sl = 0.0;
		}

		if (tr < 0.0)
		{
			sr = 0.0;
		}

		float ypl = yl;
		yl = tau1 / timePerSample_s + tau2 / (timePerSample_s*timePerSample_s);
		yl = (sl + yl * ypl + tau2 / timePerSample_s * zl) / (1.0 + yl);
		zl = (yl - ypl) / timePerSample_s;
		float ypr = yr;
		yr = tau1 / timePerSample_s + tau2 / (timePerSample_s*timePerSample_s);
		yr = (sr + yr * ypr + tau2 / timePerSample_s * zr) / (1.0 + yr);
		zr = (yr - ypr) / timePerSample_s;

		uint16_t* sampleBuffer = audioData.Data();
			
		int32_t l = 0.5 + scale * 32768.0 * yl;
		if (l > 32767)
		{
			l = 32767;
		} else if (l < -32768)
		{
			l = -32768;
		}
		sampleBuffer[2 * sample] = (uint16_t)l;

		l = 0.5 + scale * 32768.0 * yr;
		if (l > 32767)
		{
			l = 32767;
		}
		else if (l < -32768)
		{
			l = -32768;
		}
		sampleBuffer[2 * sample + 1] = (uint16_t)l;
	}
}


void ImageToSoundscapeConverter::initWaveformCacheStereo()
{
	//waveformcache
	float tau1 = 0.5 / omega[rows - 1];
	float tau2 = 0.25 * tau1*tau1;
	float q, q2;
	float yl = 0.0, yr = 0.0;
	float zl = 0.0, zr = 0.0;
	for (int sample = 0; sample < sampleCount; sample++)
	{
		if (use_bspline)
		{
			q = 1.0 * (sample % samplesPerColumn) / (samplesPerColumn - 1);
			q2 = 0.5 * q * q;
		}

		int j = sample / samplesPerColumn;
		if (j > columns - 1)
		{
			j = columns - 1;
		}

		float r = 1.0 * sample / (sampleCount - 1);  // Binaural attenuation/delay parameter
		float theta = (r - 0.5) * TwoPi / 3;
		float x = 0.5 * acoustical_size_of_head_m * (theta + sin(theta));
		float tl = sample * timePerSample_s;
		float tr = tl;
		if (use_delay)
		{
			tr += x / speed_of_sound_m_s;  // Time delay model
		}
		x = fabs(x);
		float hrtfl = 1.0, hrtfr = 1.0;

		for (int i = 0; i < rows; i++)
		{
			if (use_diffraction)
			{
				// First order frequency-dependent azimuth diffraction model
				float hrtf;
				if (TwoPi*speed_of_sound_m_s / omega[i] > x)
				{
					hrtf = 1.0;
				}
				else
				{
					hrtf = TwoPi*speed_of_sound_m_s / (x*omega[i]);
				}

				if (theta < 0.0)
				{
					hrtfl = 1.0;
					hrtfr = hrtf;
				}
				else
				{
					hrtfl = hrtf;
					hrtfr = 1.0;
				}
			}

			if (use_fade)
			{
				// Simple frequency-independent relative fade model
				hrtfl *= (1.0 - 0.7*r);
				hrtfr *= (0.3 + 0.7*r);
			}
			
			waveformCacheLeftChannel[(sample * rows) + i] = hrtfl * sin(omega[i] * tl + phi0[i]);
			waveformCacheRightChannel[(sample * rows) + i] = hrtfr * sin(omega[i] * tr + phi0[i]);
		}

	}


}