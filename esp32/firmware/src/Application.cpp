#include <Arduino.h>
#include "Application.h"
#include "Speaker.h"
#include "state_machine/DetectWakeWordState.h"

Application::Application(
    I2SSampler *sample_provider,
    IntentProcessor *intent_processor,
    Speaker *speaker,
    IndicatorLight *indicator_light
)
{
    m_sample_provider = sample_provider;
    m_intent_processor = intent_processor;
    m_speaker = speaker;
    m_indicator_light = indicator_light;

    m_detect_wake_word_state = new DetectWakeWordState(m_sample_provider, m_speaker);
    m_detect_wake_word_state->enterState();

    Serial.println("[PATCH V4] Application.cpp loaded.");
    Serial.println("[APP] Application started.");
    Serial.println("[APP] Local 7-class command model enabled.");
    Serial.println("[APP] Commands: on / off / one / two / three.");
    Serial.println("[APP] ON -> on.wav, OFF -> off.wav, ONE/TWO/THREE -> no OK sound.");
}

Application::~Application()
{
    if (m_detect_wake_word_state)
    {
        m_detect_wake_word_state->exitState();
        delete m_detect_wake_word_state;
        m_detect_wake_word_state = nullptr;
    }
}

void Application::run()
{
    if (!m_detect_wake_word_state)
    {
        vTaskDelay(10 / portTICK_PERIOD_MS);
        return;
    }

    bool handled = m_detect_wake_word_state->run();

    if (handled)
    {
        Serial.println("[APP] Command handled locally.");
    }

    // 避免 Application Task 持續佔用 CPU0，導致 task_wdt
    vTaskDelay(10 / portTICK_PERIOD_MS);
}