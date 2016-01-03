#include <sstream>
#include <ncurses.h>
#include <linux/input.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <cmath>
#include <vector>
#include <stdexcept>
#include <iostream>
#include <wiringPi.h>

#include "Options.h"
#include "KeyboardInput.h"

enum class MenuKeys: int
{
	PreviousOption = 'w',
	NextOption = 's',
	PreviousValue = 'a',
	NextValue = 'd',
	CycleValue = 'c'
};

KeyboardInput::KeyboardInput() :
	inputType(InputType::NoInput),
	fevdev(0),
	currentOptionIndex(0),
	lastEncoderValue(0),
	lastSwitchPressCount(0),
	encoder(nullptr),
	Verbose(false)
{
}


void KeyboardInput::setupRotaryEncoder()
{
	wiringPiSetup();
	encoder = setupencoder(4, 5, 6);
}

int KeyboardInput::readRotaryEncoder()
{
	int ch = ERR;
	if (encoder != nullptr)
	{
		//updateEncoders();
		usleep(100000);
		long l = encoder->value;
		if (l != lastEncoderValue)
		{
			if (Verbose)
			{
				printf("\nlastEncoderValue: %ld, new encoder value: %ld\n", lastEncoderValue, l);
			}
			
			if (l > lastEncoderValue)
			{
				ch = (int)MenuKeys::NextOption;
			}
			else if (l < lastEncoderValue)
			{
				ch = (int)MenuKeys::PreviousOption;
			}

			lastEncoderValue = l;
		}

		l = encoder->switchpresscount;
		if (l != lastSwitchPressCount)
		{
			if (Verbose)
			{
				printf("\nlastSwitchPressCount: %ld, new switchpresscount: %ld\n", lastSwitchPressCount, l);
			}
			ch = (int)MenuKeys::CycleValue;
			
			lastSwitchPressCount = l;
		}
	}

	return ch;
}

bool KeyboardInput::SetInputType(InputType inputType, std::string keyboard)
{
	this->inputType = inputType;

	if (inputType == InputType::Keyboard)
	{
		if (!grabKeyboard(keyboard))
		{
			return false;
		}
	}
	else if (inputType == InputType::RotaryEncoder)
	{
		setupRotaryEncoder();
	}

	return true;
}

bool KeyboardInput::grabKeyboard(std::string event_device_ids)
{
	std::istringstream iss(event_device_ids);

	while (!iss.eof())
	{
		std::string event_device_id;
		getline(iss, event_device_id, ',');

		int device_id = atoi(event_device_id.c_str());

		std::string devpath("/dev/input/event" + event_device_id);

		fevdev.push_back(open(devpath.c_str(), O_RDONLY | O_NONBLOCK));
		if (fevdev.back() == -1)
		{
			return false;
		}

		if (ioctl(fevdev.back(), EVIOCGRAB, 1) != 0) //grab keyboard
		{
			return false;
		}
	}


	return true;
}

void KeyboardInput::ReleaseKeyboard()
{
	for (int i = 0; i < fevdev.size(); i++)
	{
		if (fevdev[i] != -1)
		{
			ioctl(fevdev[i], EVIOCGRAB, 0); //Release grabbed keyboard
			close(fevdev[i]);
		}
	}
}


int KeyboardInput::ReadKey()
{
	if (inputType == InputType::Terminal)
	{
		return getchar();
	}
	else if (inputType == InputType::NCurses)
	{
		return getch();
	}
	else if (inputType == InputType::Keyboard)
	{
		for (int i = 0; i < fevdev.size(); i++)
		{
			if (fevdev[i] == -1)
			{
				return ERR;
			}
			struct input_event ev[2];

			//std::cout << "Read" << std::endl;
			int rd = read(fevdev[i], ev, sizeof(struct input_event) * 2);

			if (rd < 0)
			{
				continue;
			}
			//std::cout << "Ok: " << rd << std::endl;

			int value = ev[0].value;
			if (value != ' ' && ev[1].value == 1 && ev[1].type == EV_KEY) //value=1: key press, value=0 key release
			{
				return(keyEventMap(ev[1].code));
			}
		}
		return ERR;
	}
	else if (inputType == InputType::RotaryEncoder)
	{
		return readRotaryEncoder();
	}
}

std::string KeyboardInput::GetInteractiveCommandList()
{
	std::stringstream cmdlist;
	
	cmdlist << "raspivoice" << std::endl;
	cmdlist << "Press key to cycle settings:" << std::endl;
	cmdlist << "0: Mute [off, on]" << std::endl;
	cmdlist << "1: Negative image [off, on]" << std::endl;
	cmdlist << "2: Zoom [off, x2, x4]" << std::endl;
	cmdlist << "3: Blinders [off, on]" << std::endl;
	cmdlist << "4: Edge detection [off, 50%%, 100%%]" << std::endl;
	cmdlist << "5: Threshold [off, 25%%, 50%%, 75%%]" << std::endl;
	cmdlist << "6: Brightness [low, normal, high]" << std::endl;
	cmdlist << "7: Contrast [x1, x2, x3]" << std::endl;
	cmdlist << "8: Foveal mapping [off, on]" << std::endl;
	cmdlist << ".: Restore defaults" << std::endl;
	cmdlist << "q, [Escape]: Quit" << std::endl;

	return cmdlist.str();
}

std::string KeyboardInput::KeyPressedAction(int ch)
{
	std::vector<int> option_cycle{ '0', '1', '2', '3', '4', '5', '6', '7', '8', '.' }; //, '+', '-', 'q' };

	bool option_changed = false;
	int changevalue = 0; //-1: decrease value, 0: no change, 1: increase value, 2: cycle values
	std::stringstream state_str;
	int newvolume = -1;

	if (Verbose)
	{
		std::cout << "KeyPressedAction: ch = " << ch << std::endl;
	}

	//Menu navigation keys:
	switch ((MenuKeys)ch)
	{
		case MenuKeys::PreviousValue:
			changevalue = -1;
			break;
		case MenuKeys::PreviousOption:
			option_changed = true;
			if (currentOptionIndex > 0)
			{
				currentOptionIndex--;
			}
			else
			{
				currentOptionIndex = option_cycle.size() - 1;
			}
			break;
		case MenuKeys::NextValue:
			changevalue = 1;
			break;
		case MenuKeys::NextOption:
			option_changed = true;
			if (currentOptionIndex < (option_cycle.size()-1))
			{
				currentOptionIndex++;
			}
			else
			{
				currentOptionIndex = 0;
			}
			break;
		case MenuKeys::CycleValue:
			changevalue = 2;
			break;
	}

	if (option_changed)
	{
		//just speak out currently selected option
		switch (option_cycle[currentOptionIndex])
		{
			case '0':
				state_str << "mute";
				break;
			case '1':
				state_str << "negative image";
				break;
			case '2':
				state_str << "zoom";
				break;
			case '3':
				state_str << "blinders";
				break;
			case '4':
				state_str << "edge detection";
				break;
			case '5':
				state_str << "threshold";
				break;
			case '6':
				state_str << "brightness";
				break;
			case '7':
				state_str << "contrast";
				break;
			case '8':
				state_str << "foveal mapping";
				break;
			case '+':
				state_str << "volume up";
				break;
			case '-':
				state_str << "volume down";
				break;
			case ',':
			case '.':
			case 263: //Backspace
				state_str << "default options";
				break;
			case 'q':
			case 27: //ESC
				state_str << "quit";
				break;
		}
	}
	else //value change requested
	{
		if (changevalue != 0)
		{
			//use current option if navigation keys were used:
			ch = option_cycle[currentOptionIndex];
		}
		else
		{
			changevalue = 2; //cycle value if direct key was used
		}

		//change value and speak out new value:
		pthread_mutex_lock(&rvopt_mutex);
		switch (ch)
		{
			case '0':
				rvopt.mute = !rvopt.mute;
				state_str << ((rvopt.mute) ? "muted on" : "muted off");
				break;
			case '1':
				rvopt.negative_image = !rvopt.negative_image;
				state_str << ((rvopt.negative_image) ? "negative image on" : "negative image off");
				break;
			case '2':
				cycleValues(rvopt.zoom, {1.0, 2.0, 4.0}, changevalue);
				state_str << "zoom factor" << rvopt.zoom;
				break;
			case '3':
				rvopt.blinders = (rvopt.blinders == 0) ? (rvopt.columns / 4) : 0;
				state_str << (rvopt.blinders == 0) ? "blinders off" : "blinders on";
				break;
			case '4':
				cycleValues(rvopt.edge_detection_opacity, { 0.0, 0.5, 1.0 }, changevalue);
				state_str << "edge detection " << rvopt.edge_detection_opacity;
				break;
			case '5':
				cycleValues(rvopt.threshold, { 0, int(0.25*255), int(0.5*255), int(0.75*255) }, changevalue);
				state_str << "threshold " << rvopt.threshold;
				break;
			case '6':
				cycleValues(rvopt.brightness, { -100, 0, 100 }, changevalue);
				if (rvopt.brightness == 100)
				{
					state_str << "brightness high";
				}
				else if (rvopt.brightness == 0)
				{
					state_str << "brightness medium";
				}
				else
				{
					state_str << "brightness low";
				}
				break;
			case '7':
				cycleValues(rvopt.contrast, { 1.0, 2.0, 3.0 }, changevalue);
				state_str << "contrast factor " << rvopt.contrast;
				break;
			case '8':
				rvopt.foveal_mapping = !rvopt.foveal_mapping;
				state_str << (rvopt.foveal_mapping ? "foveal mapping on" : "foveal mapping off");
				break;
			case '+':
				cycleValues(rvopt.volume, { 1, 2, 4, 8, 16, 32, 64, 100 }, (changevalue > 0) ? 1: -1);
				newvolume = rvopt.volume;
				state_str << "Volume up ";
				break;
			case '-':
				cycleValues(rvopt.volume, { 1, 2, 4, 8, 16, 32, 64, 100 }, (changevalue > 0) ? -1 : 1);
				newvolume = rvopt.volume;
				state_str << "Volume down ";
				break;
			case ',':
			case '.':
			case 263:
				rvopt = GetCommandLineOptions();
				state_str << "default options";
				break;
			case 'q':
			case 27: // ESC key
				state_str << "goodbye";
				rvopt.quit = true;
				break;
		}
		pthread_mutex_unlock(&rvopt_mutex);
	}

	return state_str.str();
}


int KeyboardInput::keyEventMap(int event_code)
{
	if (Verbose)
	{
		//event codes see linux/input.h header file
		std::cout << "KeyEventMap: event_code = " << event_code << std::endl;
	}

	int ch = 0;
	switch (event_code)
	{
		case KEY_A:
		case KEY_LEFT:
		case KEY_BACK:
		case KEY_STOP:
		case KEY_F1:
			ch = (int)MenuKeys::PreviousValue;
			break;
		case KEY_S:
		case KEY_DOWN:
		case KEY_FORWARD:
		case KEY_NEXTSONG:
		case KEY_F3:
			ch = (int)MenuKeys::NextOption;
			break;
		case KEY_D:
		case KEY_RIGHT:
		case KEY_PLAYPAUSE:
		case KEY_PLAY:
		case KEY_PAUSE:
		case BTN_RIGHT:
			ch = (int)MenuKeys::NextValue;
			break;
		case KEY_W:
		case KEY_UP:
		case KEY_PREVIOUSSONG:
		case KEY_REWIND:
		case KEY_HOME:
			ch = (int)MenuKeys::PreviousOption;
			break;
		case KEY_LINEFEED:
		case KEY_KPENTER:
		case KEY_SPACE:
		case BTN_LEFT:
			ch = (int)MenuKeys::CycleValue;
			break;
		case KEY_0:
		case KEY_KP0:
		case KEY_MUTE:
		case KEY_NUMERIC_0:
			ch = '0';
			break;
		case KEY_1:
		case KEY_KP1:
			ch = '1';
			break;
		case KEY_2:
		case KEY_KP2:
			ch = '2';
			break;
		case KEY_3:
		case KEY_KP3:
			ch = '3';
			break;
		case KEY_4:
		case KEY_KP4:
			ch = '4';
			break;
		case KEY_5:
		case KEY_KP5:
			ch = '5';
			break;
		case KEY_6:
		case KEY_KP6:
			ch = '6';
			break;
		case KEY_7:
		case KEY_KP7:
			ch = '7';
			break;
		case KEY_8:
		case KEY_KP8:
			ch = '8';
			break;
		case KEY_9:
		case KEY_KP9:
			ch = '9';
			break;
		case KEY_NUMERIC_STAR:
		case KEY_KPASTERISK:
			ch = '*';
			break;
		case KEY_SLASH:
		case KEY_KPSLASH:
			ch = '/';
			break;
		case KEY_EQUAL:
		case KEY_KPEQUAL:
			ch = '=';
			break;
		case KEY_DOT:
		case KEY_KPDOT:
		case KEY_KPCOMMA:
		case KEY_KPJPCOMMA:
		case KEY_BACKSPACE:
		case KEY_DC:
			ch = '.';
			break;
		case KEY_KPPLUS:
		case KEY_VOLUMEUP:
			ch = '+';
			break;
		case KEY_MINUS:
		case KEY_KPMINUS:
		case KEY_VOLUMEDOWN:
			ch = '-';
			break;
	}

	return ch;
}

int KeyboardInput::changeIndex(int i, int maxindex, int changevalue)
{
	int new_index = 0;

	if (changevalue == -1) //decrease (stop at 0)
	{
		new_index = i - 1;
		if (new_index < 0)
		{
			new_index = 0;
		}
	}
	else if (changevalue == 1) //increase (stop at max)
	{
		new_index = i + 1;
		if (new_index > maxindex)
		{
			new_index = maxindex;
		}
	}
	else if (changevalue == 2)  //increase (continue at 0)
	{
		new_index = i + 1;
		if (new_index > maxindex)
		{
			new_index = 0;
		}
	}
	else if (changevalue == -2) //decrease (continue at max)
	{
		new_index = i - 1;
		if (new_index < 0)
		{
			new_index = maxindex;
		}
	}

	return new_index;
}

void KeyboardInput::cycleValues(float &current_value, std::vector<float> value_list, int changevalue)
{
	for (int i = 0; i < value_list.size(); i++)
	{
		if (fabs(current_value - value_list[i]) < 1e-10)
		{
			current_value = value_list[changeIndex(i, value_list.size() - 1, changevalue)];
			return;
		}
	}
	current_value = value_list[0];
}

void KeyboardInput::cycleValues(int &current_value, std::vector<int> value_list, int changevalue)
{
	for (int i = 0; i < value_list.size(); i++)
	{
		if (current_value == value_list[i])
		{
			current_value = value_list[changeIndex(i, value_list.size() - 1, changevalue)];
			return;
		}
	}
	current_value = value_list[0];
}
