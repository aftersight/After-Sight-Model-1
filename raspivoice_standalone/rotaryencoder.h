/*
Updated version including press switch functionality
based on:
rotaryencoder by astine
http://theatticlight.net/posts/Reading-a-Rotary-Encoder-from-a-Raspberry-Pi/
https://github.com/astine/rotaryencoder
*/

#pragma once

//17 pins / 3 pins per encoder = 5 maximum encoders
#define max_encoders 5

struct encoder
{
   int pin_a;
   int pin_b;
   int pin_switch;
   volatile long value;
   volatile long switchpresscount;
   volatile int lastEncoded;
   volatile unsigned long lasttime;
};

extern struct encoder encoders[max_encoders];

/*
Should be run for every rotary encoder you want to control
Returns a pointer to the new rotary encoder structer
The pointer will be NULL is the function failed for any reason
*/
struct encoder *setupencoder(int pin_a, int pin_b, int pin_switch);
