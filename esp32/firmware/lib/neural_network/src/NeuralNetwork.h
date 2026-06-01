#ifndef NEURAL_NETWORK_H
#define NEURAL_NETWORK_H

#include <stdint.h>

struct TfLiteTensor;

namespace tflite
{
    class ErrorReporter;
    class MicroInterpreter;
    class AllOpsResolver;
    struct Model;
}

class NeuralNetwork
{
public:
    NeuralNetwork();
    ~NeuralNetwork();

    float *getInputBuffer();

    float predict();

    int getLastCommandIndex();
    float getLastCommandScore();
    const char *getLastCommandLabel();

private:
    float readOutputValue(int index);

    tflite::ErrorReporter *m_error_reporter;
    const tflite::Model *m_model;
    tflite::MicroInterpreter *m_interpreter;
    tflite::AllOpsResolver *m_resolver;

    uint8_t *m_tensor_arena;

    TfLiteTensor *input;
    TfLiteTensor *output;

    int m_last_command_index;
    float m_last_command_score;
};

#endif
