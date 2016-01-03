#pragma once

#include <string>
#include "rotaryencoder.h"
#include "Options.h"

class KeyboardInput
{
public:
	enum class InputType
	{
		NoInput = 0,
		Terminal,
		NCurses,
		Keyboard,
		RotaryEncoder
	};

private:
	std::vector<int> fevdev;
	int currentOptionIndex;
	struct encoder *encoder;
	InputType inputType;
	long lastEncoderValue;
	long lastSwitchPressCount;

	void setupRotaryEncoder();
	int readRotaryEncoder();
	bool grabKeyboard(std::string bus_device_id);
	int keyEventMap(int event_code);
	int changeIndex(int i, int maxindex, int changevalue);
	void cycleValues(int &current_value, std::vector<int> value_list, int changevalue);
	void cycleValues(float &current_value, std::vector<float> value_list, int changevalue);
public:
	bool Verbose;

	KeyboardInput();
	bool SetInputType(InputType, std::string keyboard = "");
	std::string KeyPressedAction(int ch);
	void ReleaseKeyboard();
	int ReadKey();
	std::string GetInteractiveCommandList();
};

