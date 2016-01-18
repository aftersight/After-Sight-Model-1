#pragma once

#include <vector>
#include <raspicam/raspicam_cv.h>
#include <opencv/cv.h>
#include <opencv/highgui.h>

#include "Options.h"
#include "ImageToSoundscape.h"

class RaspiVoice
{
private:
	int rows;
	int columns;
	int image_source;
	bool preview;
	bool use_bw_test_image;
	bool verbose;
	RaspiVoiceOptions opt;

	ImageToSoundscapeConverter *i2ssConverter;
	raspicam::RaspiCam_Cv raspiCam;
	cv::VideoCapture cap;
	std::vector<float> *image;

	RaspiVoice(const RaspiVoice& other) = delete;
	RaspiVoice& operator=(const RaspiVoice&) = delete;

	void init();
	void initFileImage();
	void initTestImage();
	void initRaspiCam();
	void initUsbCam();
	cv::Mat readImage();
	void processImage(cv::Mat rawImage);
	int playWav(std::string filename);
public:
	RaspiVoice(RaspiVoiceOptions opt);
	~RaspiVoice();
	void GrabAndProcessFrame(RaspiVoiceOptions opt);
	void PlayFrame(RaspiVoiceOptions opt);
};

