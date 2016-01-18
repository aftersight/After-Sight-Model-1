/*
Updated version including press switch functionality
based on:
rotaryencoder by astine
http://theatticlight.net/posts/Reading-a-Rotary-Encoder-from-a-Raspberry-Pi/
https://github.com/astine/rotaryencoder
*/
#include <wiringPi.h>

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#include "rotaryencoder.h"
#include <chrono>
void updateEncoders(void);
void updateSwitch(void);

//Pre-allocate encoder objects on the stack so we don't have to 
//worry about freeing them
struct encoder encoders[max_encoders];

int numberofencoders = 0;

void updateEncoders()
{
   struct encoder *encoder = encoders;
   unsigned long nowTime = std::chrono::system_clock::now().time_since_epoch() /
                           std::chrono::milliseconds(1);   
   for (; encoder < encoders + numberofencoders; encoder++)
   {
      int MSB = digitalRead(encoder->pin_a);
      int LSB = digitalRead(encoder->pin_b);

      int encoded = (MSB << 1) | LSB;
      int sum = (encoder->lastEncoded << 2) | encoded;
      if ((nowTime - encoder->lasttime) < 200)
      {

         encoder->lasttime = nowTime;
         encoder->lastEncoded = encoded;
         break;
      }
      encoder->lasttime = nowTime;

      if (sum == 0b1101 || sum == 0b0100 || sum == 0b0010 || sum == 0b1011) encoder->value++;
      if (sum == 0b1110 || sum == 0b0111 || sum == 0b0001 || sum == 0b1000) encoder->value--;

      encoder->lastEncoded = encoded;
   }
}

void updateSwitch()
{
   struct encoder *encoder = encoders;
   unsigned long nowTime = std::chrono::system_clock::now().time_since_epoch() /
                           std::chrono::milliseconds(1);
   
   for (; encoder < encoders + numberofencoders; encoder++)
   {
      int pin_state = digitalRead(encoder->pin_switch);
      if (pin_state == LOW)
      {
         //TODO: Debounce with millis() ? 
         if ((nowTime - encoder->lasttime) > 200)
         {

            encoder->switchpresscount++;
         }
         encoder->lasttime = nowTime;
      }
   }
}

struct encoder *setupencoder(int pin_a, int pin_b, int pin_switch = -1)
{
   if (numberofencoders > max_encoders)
   {
      printf("Maximum number of encodered exceded: %i\n", max_encoders);
      return NULL;
   }

   struct encoder *newencoder = encoders + numberofencoders++;
   newencoder->pin_a = pin_a;
   newencoder->pin_b = pin_b;
   newencoder->pin_switch = pin_switch;
   newencoder->value = 0;
   newencoder->lastEncoded = 0;
   newencoder->switchpresscount = 0;
   newencoder->lasttime = 0;

   pinMode(pin_a, INPUT);
   pinMode(pin_b, INPUT);
   pullUpDnControl(pin_a, PUD_UP);
   pullUpDnControl(pin_b, PUD_UP);
   wiringPiISR(pin_a, INT_EDGE_BOTH, updateEncoders);
   wiringPiISR(pin_b, INT_EDGE_BOTH, updateEncoders);
   if (pin_switch != -1)
   {
      pinMode(pin_switch, INPUT);
      pullUpDnControl(pin_switch, PUD_UP);
      wiringPiISR(pin_switch, INT_EDGE_FALLING, updateSwitch);
   }

   return newencoder;
}
