#include <Arduino.h>
#undef DEFAULT

#include "NeuralNetwork.h"
#include "model.h"

#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"

#include "esp_heap_caps.h"

#include <stdint.h>

extern const unsigned char converted_model_tflite[];
extern const unsigned int converted_model_tflite_len;

static const int kArenaSize = 100 * 1024;

static const int kCommandClassCount = 7;

static const char *kCommandLabels[kCommandClassCount] = {
    "on",
    "off",
    "one",
    "two",
    "three",
    "unknown",
    "_background"
};

NeuralNetwork::NeuralNetwork()
{
    Serial.println("[PATCH V2] NeuralNetwork.cpp loaded.");

    m_error_reporter = nullptr;
    m_model = nullptr;
    m_interpreter = nullptr;
    m_resolver = nullptr;
    m_tensor_arena = nullptr;
    input = nullptr;
    output = nullptr;
    m_last_command_index = -1;
    m_last_command_score = 0.0f;

    m_error_reporter = new tflite::MicroErrorReporter();

    m_tensor_arena = (uint8_t *)heap_caps_malloc(
        kArenaSize,
        MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT
    );

    if (!m_tensor_arena)
    {
        Serial.println("[ERROR] Failed to allocate PSRAM tensor arena");
        return;
    }

    TF_LITE_REPORT_ERROR(m_error_reporter, "Loading model");

    m_model = tflite::GetModel(converted_model_tflite);

    if (m_model->version() != TFLITE_SCHEMA_VERSION)
    {
        TF_LITE_REPORT_ERROR(
            m_error_reporter,
            "Model schema version %d != supported version %d.",
            m_model->version(),
            TFLITE_SCHEMA_VERSION
        );
        return;
    }

    m_resolver = new tflite::AllOpsResolver();

    m_interpreter = new tflite::MicroInterpreter(
        m_model,
        *m_resolver,
        m_tensor_arena,
        kArenaSize,
        m_error_reporter
    );

    TfLiteStatus allocate_status = m_interpreter->AllocateTensors();

    if (allocate_status != kTfLiteOk)
    {
        TF_LITE_REPORT_ERROR(m_error_reporter, "AllocateTensors() failed");
        input = nullptr;
        output = nullptr;
        return;
    }

    size_t used_bytes = m_interpreter->arena_used_bytes();
    TF_LITE_REPORT_ERROR(m_error_reporter, "Used bytes %d\n", used_bytes);

    input = m_interpreter->input(0);
    output = m_interpreter->output(0);

    Serial.print("Input dims: ");
    for (int i = 0; i < input->dims->size; i++)
    {
        Serial.printf("%d ", input->dims->data[i]);
    }
    Serial.println();

    Serial.printf("Input type: %d\n", input->type);

    Serial.print("Output dims: ");
    for (int i = 0; i < output->dims->size; i++)
    {
        Serial.printf("%d ", output->dims->data[i]);
    }
    Serial.println();

    Serial.printf("Output type: %d\n", output->type);
    Serial.printf("Output scale: %.8f\n", output->params.scale);
    Serial.printf("Output zero_point: %d\n", output->params.zero_point);
}

NeuralNetwork::~NeuralNetwork()
{
    delete m_interpreter;
    m_interpreter = nullptr;

    delete m_resolver;
    m_resolver = nullptr;

    if (m_tensor_arena)
    {
        heap_caps_free(m_tensor_arena);
        m_tensor_arena = nullptr;
    }

    delete m_error_reporter;
    m_error_reporter = nullptr;
}

float *NeuralNetwork::getInputBuffer()
{
    if (!input)
    {
        return nullptr;
    }

    if (input->type != kTfLiteFloat32)
    {
        Serial.printf("[ERROR] input tensor type is not float32: %d\n", input->type);
        return nullptr;
    }

    return input->data.f;
}

float NeuralNetwork::readOutputValue(int index)
{
    if (!output || index < 0)
    {
        return 0.0f;
    }

    if (output->type == kTfLiteFloat32)
    {
        return output->data.f[index];
    }

    if (output->type == kTfLiteInt8)
    {
        int8_t raw = output->data.int8[index];
        return (raw - output->params.zero_point) * output->params.scale;
    }

    if (output->type == kTfLiteUInt8)
    {
        uint8_t raw = output->data.uint8[index];
        return (static_cast<int>(raw) - output->params.zero_point) * output->params.scale;
    }

    return 0.0f;
}

float NeuralNetwork::predict()
{
    if (!m_interpreter || !input || !output)
    {
        Serial.println("[ERROR] NeuralNetwork not ready");
        m_last_command_index = -1;
        m_last_command_score = 0.0f;
        return 0.0f;
    }

    TfLiteStatus invoke_status = m_interpreter->Invoke();

    if (invoke_status != kTfLiteOk)
    {
        TF_LITE_REPORT_ERROR(m_error_reporter, "Invoke failed");
        m_last_command_index = -1;
        m_last_command_score = 0.0f;
        return 0.0f;
    }

    int output_count = 1;
    for (int i = 0; i < output->dims->size; i++)
    {
        output_count *= output->dims->data[i];
    }

    int count = output_count;
    if (count > kCommandClassCount)
    {
        count = kCommandClassCount;
    }

    float best_score = -999999.0f;
    int best_index = -1;

    Serial.print("[RAW] ");
    for (int i = 0; i < count; i++)
    {
        float score = readOutputValue(i);
        Serial.printf("%s=%.2f ", kCommandLabels[i], score);

        if (score > best_score)
        {
            best_score = score;
            best_index = i;
        }
    }
    Serial.println();

    m_last_command_index = best_index;
    m_last_command_score = best_score;

    return best_score;
}

int NeuralNetwork::getLastCommandIndex()
{
    return m_last_command_index;
}

float NeuralNetwork::getLastCommandScore()
{
    return m_last_command_score;
}

const char *NeuralNetwork::getLastCommandLabel()
{
    if (m_last_command_index < 0 || m_last_command_index >= kCommandClassCount)
    {
        return "invalid";
    }

    return kCommandLabels[m_last_command_index];
}
