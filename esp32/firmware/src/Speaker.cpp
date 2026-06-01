#include <Arduino.h>
#include "Speaker.h"
#include "I2SOutput.h"
#include "WAVFileReader.h"

Speaker::Speaker(I2SOutput *i2s_output)
{
    m_i2s_output = i2s_output;

    m_ok = new WAVFileReader("/ok.wav");
    m_ready_ping = new WAVFileReader("/ready_ping.wav");
    m_cantdo = new WAVFileReader("/cantdo.wav");
    m_light_on = new WAVFileReader("/light_on.wav");
    m_light_off = new WAVFileReader("/light_off.wav");
    m_life = new WAVFileReader("/life.wav");

    m_jokes[0] = new WAVFileReader("/joke0.wav");
    m_jokes[1] = new WAVFileReader("/joke1.wav");
    m_jokes[2] = new WAVFileReader("/joke2.wav");
    m_jokes[3] = new WAVFileReader("/joke3.wav");

    // 不讀 on.wav / off.wav，避免格式錯誤
    // 不讀 joke4.wav，避免你之前的 joke4.wav 錯誤
}

Speaker::~Speaker()
{
    delete m_ok;
    delete m_ready_ping;
    delete m_cantdo;
    delete m_light_on;
    delete m_light_off;
    delete m_life;

    delete m_jokes[0];
    delete m_jokes[1];
    delete m_jokes[2];
    delete m_jokes[3];
}

void Speaker::playOK()
{
    if (!m_i2s_output || !m_ok)
    {
        return;
    }

    Serial.println("[SPEAKER] playOK");
    m_ok->reset();
    m_i2s_output->setSampleGenerator(m_ok);
}

void Speaker::playReady()
{
    if (!m_i2s_output || !m_ready_ping)
    {
        return;
    }

    Serial.println("[SPEAKER] playReady");
    m_ready_ping->reset();
    m_i2s_output->setSampleGenerator(m_ready_ping);
}

void Speaker::playCantDo()
{
    if (!m_i2s_output || !m_cantdo)
    {
        return;
    }

    Serial.println("[SPEAKER] playCantDo");
    m_cantdo->reset();
    m_i2s_output->setSampleGenerator(m_cantdo);
}

void Speaker::playLightOn()
{
    if (!m_i2s_output || !m_light_on)
    {
        return;
    }

    Serial.println("[SPEAKER] playLightOn");
    m_light_on->reset();
    m_i2s_output->setSampleGenerator(m_light_on);
}

void Speaker::playLightOff()
{
    if (!m_i2s_output || !m_light_off)
    {
        return;
    }

    Serial.println("[SPEAKER] playLightOff");
    m_light_off->reset();
    m_i2s_output->setSampleGenerator(m_light_off);
}

void Speaker::playRandomJoke()
{
    if (!m_i2s_output)
    {
        return;
    }

    int joke = random(4);

    Serial.printf("[SPEAKER] playRandomJoke %d\n", joke);
    m_jokes[joke]->reset();
    m_i2s_output->setSampleGenerator(m_jokes[joke]);
}

void Speaker::playLife()
{
    if (!m_i2s_output || !m_life)
    {
        return;
    }

    Serial.println("[SPEAKER] playLife");
    m_life->reset();
    m_i2s_output->setSampleGenerator(m_life);
}