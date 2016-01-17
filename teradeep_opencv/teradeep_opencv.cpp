#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <unistd.h>
#include <pthread.h>
#include <ft2build.h>
#include FT_FREETYPE_H
#include <opencv2/opencv.hpp>
extern "C" {
#include "thnets.h"
}

#include <sys/stat.h>

#include <cstdio>
#include <fcntl.h>
#include <iostream>
#include <fstream>
bool FileExists(char* filename) 
{
    struct stat fileInfo;
    return stat(filename, &fileInfo) == 0;
}

using namespace cv;

#define NBUFFERS 4
static int frame_width, frame_height, win_width, win_height;
static FT_Library ft_lib;
static FT_Face ft_face;

static double seconds()
{
	static double base;
	struct timeval tv;

	gettimeofday(&tv, 0);
	if(!base)
		base = tv.tv_sec + tv.tv_usec * 1e-6;
	return tv.tv_sec + tv.tv_usec * 1e-6 - base;
}

struct catp {
	float p;
	char *cat;
};

int catpcmp(const void *a, const void *b)
{
	return (((struct catp *)b)->p - ((struct catp *)a)->p) * 1e8;
}

char **categories;
int ncat;

int loadcategories(const char *modelsdir)
{
	char path[200], s[200], *p;
	FILE *fp;
	
	sprintf(path, "%s/categories.txt", modelsdir);
	fp = fopen(path, "r");
	if(!fp)
		THError("Cannot load %s", path);
	ncat = 0;
	if(fgets(s, sizeof(s), fp))
	while(fgets(s, sizeof(s), fp))
	{
		p = strchr(s, ',');
		if(!p)
			continue;
		ncat++;
	}
	rewind(fp);
	categories = (char **)calloc(ncat, sizeof(*categories));
	ncat = 0;
	if(fgets(s, sizeof(s), fp))
	while(fgets(s, sizeof(s), fp))
	{
		p = strchr(s, ',');
		if(!p)
			continue;
		*p = 0;
		categories[ncat++] = strdup(s);
	}
	fclose(fp);
	return 0;
}

static void loadfont()
{
	if(FT_Init_FreeType(&ft_lib))
	{
		fprintf(stderr, "Error initializing the FreeType library\n");
		return;
	}
	if(FT_New_Face(ft_lib, "/usr/share/fonts/truetype/freefont/FreeSans.ttf", 0, &ft_face))
	{
		fprintf(stderr, "Error loading FreeSans font\n");
		return;
	}
}

static int text(Mat *frame, int x, int y, const char *text, int size, int color)
{
	if(!ft_face)
		return -1;

	int i, stride, asc;
	unsigned j, k;
	unsigned char red = (color >> 16);
	unsigned char green = (color >> 8);
	unsigned char blue = color;
	FT_Set_Char_Size(ft_face, 0, size * 64, 0, 0 );
	int scale = ft_face->size->metrics.y_scale;
	asc = FT_MulFix(ft_face->ascender, scale) / 64;
	stride = frame->step1(0);
	FT_Set_Char_Size(ft_face, 0, 64 * size, 0, 0);
	unsigned char *pbitmap = frame->data + stride * y + x * 3, *p;
	for(i = 0; text[i]; i++)
	{
		FT_Load_Char(ft_face, text[i], FT_LOAD_RENDER);
		FT_Bitmap *bmp = &ft_face->glyph->bitmap;
		for(j = 0; j < bmp->rows; j++)
			for(k = 0; k < bmp->width; k++)
			{
				p = pbitmap + (j + asc - ft_face->glyph->bitmap_top) * stride + 3 * (k + ft_face->glyph->bitmap_left);
				p[0] = (bmp->buffer[j * bmp->pitch + k] * red + (255 - bmp->buffer[j * bmp->pitch + k]) * p[0]) / 255;
				p[1] = (bmp->buffer[j * bmp->pitch + k] * green + (255 - bmp->buffer[j * bmp->pitch + k]) * p[1]) / 255;
				p[2] = (bmp->buffer[j * bmp->pitch + k] * blue + (255 - bmp->buffer[j * bmp->pitch + k]) * p[2]) / 255;
			}
		pbitmap += 3 * (ft_face->glyph->advance.x / 64);
	}
	return 0;
}

int main(int argc, char **argv)
{
	THNETWORK *net;
	int alg = 1, i;
	char camera[6] = "cam0";
	const char *modelsdir = 0, *inputfile = camera;
	const int eye = 231;
	const char *winname = "thnets opencv demo";

	frame_width = 640;
	frame_height = 480;
	loadfont();
	for(i = 1; i < argc; i++)
	{
		if(argv[i][0] != '-')
			continue;
		switch(argv[i][1])
		{
		case 'm':
			if(i+1 < argc)
				modelsdir = argv[++i];
			break;
		case 'i':
			if(i+1 < argc)
				inputfile = argv[++i];
			break;
		case 'a':
			if(i+1 < argc)
				alg = atoi(argv[++i]);
			break;
		case 'r':
			if(i+1 < argc)
			{
				i++;
				if(!strcasecmp(argv[i], "QVGA"))
				{
					frame_width = 320;
					frame_height = 240;
				} else if(!strcasecmp(argv[i], "HD"))
				{
					frame_width = 1280;
					frame_height = 720;
				} else if(!strcasecmp(argv[i], "FHD"))
				{
					frame_width = 1920;
					frame_height = 1080;
				}
			}
			break;
		}
	}
	if(!modelsdir || !inputfile)
	{
		fprintf(stderr, "Syntax: thnetsdemo -m <models directory> [-i <input file (default cam0)>]\n");
		fprintf(stderr, "                   [-a <alg=0:norm,1:MM,default,2:cuDNN,3:cudNNhalf>]\n");
		fprintf(stderr, "                   [-r <QVGA,VGA (default),HD,FHD] [-f(ullscreen)]\n");
		return -1;
	}
	if(alg == 3)
	{
		alg = 2;
		THCudaHalfFloat(1);
	}
	THInit();
	net = THLoadNetwork(modelsdir);
	loadcategories(modelsdir);
	if(net)
	{
		THMakeSpatial(net);
		if(alg == 0)
			THUseSpatialConvolutionMM(net, 0);
		else if(alg == 2)
		{
			THNETWORK *net2 = THCreateCudaNetwork(net);
			if(!net2)
				THError("CUDA not compiled in");
			THFreeNetwork(net);
			net = net2;
		}
/*		if(memcmp(inputfile, "cam", 3))
			THError("Only cams supported for now");
		VideoCapture cap(atoi(inputfile+3));
		if(!cap.isOpened())
			THError("Cannot open video device");
		cap.set(CV_CAP_PROP_FRAME_WIDTH, frame_width);
		cap.set(CV_CAP_PROP_FRAME_HEIGHT, frame_height);
		win_width = frame_width;
		win_height = frame_height; */
		int offset = (frame_width - frame_height) / 2;
		struct catp *res = (struct catp *)malloc(sizeof(*res) * ncat);
		
		Mat frame;
		float fps = 1;
		char frame_fname[50] = "/dev/shm/tera_frame", out_fname[50] = "/dev/shm/teradeep.txt", text_fname[50] = "/dev/shm/tera_text";
		for(;;)
		{
						if (FileExists(frame_fname) && !FileExists(text_fname)) {
			float *result;
			double t;
			int outwidth, outheight, n;
			char s[300];

			t = seconds();
//			cap >> frame;
frame = cv::imread(inputfile, CV_LOAD_IMAGE_COLOR);
			Rect roi(offset, 0, frame_height, frame_height);
			Mat cropped = frame(roi);
			Mat resized;
			resize(frame, resized, Size(eye, eye));
			n = THProcessImages(net, &resized.data, 1, eye, eye, 3*eye, &result, &outwidth, &outheight);
			if(n / outwidth != ncat)
				THError("Bug: wrong number of outputs received: %d != %d", n / outwidth, ncat);
			if(outheight != 1)
				THError("Bug: outheight expected 1");
			for(i = 0; i < ncat; i++)
			{
				res[i].p = result[i];
				res[i].cat = categories[i];
			}
			qsort(res, ncat, sizeof(*res), catpcmp);
//			sprintf(s, "%.2f fps", fps);
//			text(&cropped, 10, 10, s, 16, 0xff0000);
std::ofstream outfile (out_fname);
if (!outfile.is_open())
THError("Could not create out file");
			for(i = 0; i < 3; i++)
			{
//				text(&cropped, 10, 40 + i * 20, res[i].cat, 16, 0x00a000);

				sprintf(s, "%.0f\t%s\n", res[i].p * 100, res[i].cat);
//				text(&cropped, 100, 40 + i * 20, s, 16, 0x00a000);
//printf("%s %s\n",res[i].cat,s);
outfile << s;
			}
//			imshow(winname, cropped);
//			waitKey(1);
			fps = 1.0 / (seconds() - t);
			outfile.close();
			mknod(text_fname, S_IFREG | 0666, 0);
			std::remove("/dev/shm/tera_frame");
			}
		}
	} else printf("The network could not be loaded: %d\n", THLastError());
	return 0;
}
