#ifndef _indicator_light_h_
#define _indicator_light_h_

#include <Arduino.h>

enum IndicatorState
{
    OFF,
    ON,
    PULSING
};

class IndicatorLight
{
private:
    IndicatorState m_state;
    TaskHandle_t m_taskHandle;

public:
    IndicatorLight();
    void setState(IndicatorState state);
    IndicatorState getState();
};

#endif