UNAME_P := $(shell uname -p)

OPENBLASPATH=/usr/local/lib

CFLAGS = -O3 -Wall -c -fopenmp -fPIC -I../thnets -I/usr/include/freetype2
LIBS = -L$(OPENBLASPATH) -lopenblas -lm -lpthread -lfreetype -lopencv_highgui -lopencv_core -lopencv_imgproc
CC = g++

ifneq ($(filter aarc% arm%,$(UNAME_P)),)
	CFLAGS += -mfpu=neon -DUSEGLES2
	LIBS += -lEGL -lGLESv2
else
	LIBS += -lGL
endif

.PHONY : all
all : teradeep_opencv

.cpp.o:
	$(CC) $(CFLAGS) $<

teradeep_opencv: $(LIBOBJS) teradeep_opencv.o
	$(CC) -o $@ teradeep_opencv.o $(LIBS) -L/usr/local/lib -lthnets

.PHONY : clean
clean :
	rm -f *.o teradeep_opencv
