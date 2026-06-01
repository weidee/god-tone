#ifndef APPLICATION_H
#define APPLICATION_H

class I2SSampler;
class IntentProcessor;
class Speaker;
class IndicatorLight;
class DetectWakeWordState;

class Application
{
public:
    Application(
        I2SSampler *sample_provider,
        IntentProcessor *intent_processor,
        Speaker *speaker,
        IndicatorLight *indicator_light
    );

    ~Application();

    void run();

private:
    I2SSampler *m_sample_provider;
    IntentProcessor *m_intent_processor;
    Speaker *m_speaker;
    IndicatorLight *m_indicator_light;
    DetectWakeWordState *m_detect_wake_word_state;
};

#endif