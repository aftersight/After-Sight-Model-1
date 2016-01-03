#include "printtime.h"

void printtime(std::string msg)
{
	static struct timeval time;
	struct timeval newtime;
	gettimeofday(&newtime, NULL);
	if (msg != "")
	{
		std::cout << (float)(newtime.tv_sec - time.tv_sec)*1000.0 + (float)(newtime.tv_usec - time.tv_usec) * 1.0e-3 << " ms" << std::endl << msg << std::endl;
	}
	time = newtime;
}
