#ifndef DETECT_WAKE_WORD_STATE_H
#define DETECT_WAKE_WORD_STATE_H

class I2SSampler;
class AudioProcessor;
class NeuralNetwork;
class Speaker;

class DetectWakeWordState
{
public:
    DetectWakeWordState(I2SSampler *sample_provider, Speaker *speaker);

    void enterState();
    bool run();
    void exitState();

private:
    I2SSampler *m_sample_provider;
    Speaker *m_speaker;
    AudioProcessor *m_audio_processor;
    NeuralNetwork *m_nn;

    float m_average_detect_time;
    int m_number_of_runs;
    int m_number_of_detections;
};

#endif