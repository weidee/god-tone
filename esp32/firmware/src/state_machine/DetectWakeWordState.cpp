#include <Arduino.h>
#include "I2SSampler.h"
#include "AudioProcessor.h"
#include "NeuralNetwork.h"
#include "RingBuffer.h"
#include "Speaker.h"
#include "DetectWakeWordState.h"

#define WINDOW_SIZE 320
#define STEP_SIZE 160
#define POOLING_SIZE 6
#define AUDIO_LENGTH 16000

#define COMMAND_COOLDOWN_MS 1200

// 如果 LED 沒反應，再改這個腳位
#define LED_PIN 2
#define LED_PWM_CHANNEL 0
#define LED_PWM_FREQ 5000
#define LED_PWM_RESOLUTION 8

// 模型輸出 1 x 7
#define CMD_ON 0
#define CMD_OFF 1
#define CMD_ONE 2
#define CMD_TWO 3
#define CMD_THREE 4
#define CMD_UNKNOWN 5
#define CMD_BACKGROUND 6

static void setupLocalLed()
{
    ledcSetup(LED_PWM_CHANNEL, LED_PWM_FREQ, LED_PWM_RESOLUTION);
    ledcAttachPin(LED_PIN, LED_PWM_CHANNEL);
    ledcWrite(LED_PWM_CHANNEL, 0);

    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
}

static void setLocalLed(uint8_t brightness)
{
    ledcWrite(LED_PWM_CHANNEL, brightness);

    if (brightness > 0)
    {
        digitalWrite(LED_PIN, HIGH);
    }
    else
    {
        digitalWrite(LED_PIN, LOW);
    }
}

static float commandThreshold(int command)
{
    if (command == CMD_ON)
    {
        return 0.50f;
    }

    if (command == CMD_OFF)
    {
        return 0.50f;
    }

    if (command == CMD_ONE)
    {
        return 0.50f;
    }

    if (command == CMD_TWO)
    {
        return 0.50f;
    }

    if (command == CMD_THREE)
    {
        return 0.50f;
    }

    return 0.90f;
}

DetectWakeWordState::DetectWakeWordState(I2SSampler *sample_provider, Speaker *speaker)
{
    m_sample_provider = sample_provider;
    m_speaker = speaker;

    m_audio_processor = nullptr;
    m_nn = nullptr;

    m_average_detect_time = 0;
    m_number_of_runs = 0;
    m_number_of_detections = 0;
}

void DetectWakeWordState::enterState()
{
    Serial.println("[PATCH V6] DetectWakeWordState.cpp loaded.");
    Serial.println("[SERIAL MODE] Windows will receive plain ON / OFF lines.");

    m_audio_processor = new AudioProcessor(AUDIO_LENGTH, WINDOW_SIZE, STEP_SIZE, POOLING_SIZE);
    Serial.println("Created audio processor");

    m_nn = new NeuralNetwork();
    Serial.println("Created Neural Net");

    setupLocalLed();

    m_number_of_detections = 0;

    Serial.println("ESP32 local command mode ready.");
    Serial.println("Commands: ON / OFF / ONE / TWO / THREE");
    Serial.println("Serial output rule:");
    Serial.println("CMD_ON  -> print plain line: ON");
    Serial.println("CMD_OFF -> print plain line: OFF");
    Serial.println("ONE/TWO/THREE -> only LED, no Windows trigger.");
}

bool DetectWakeWordState::run()
{
    static unsigned long last_command_time = 0;

    if (!m_nn || !m_audio_processor || !m_sample_provider)
    {
        return false;
    }

    long start = millis();

    RingBufferAccessor *reader = m_sample_provider->getRingBufferReader();

    if (!reader)
    {
        return false;
    }

    reader->rewind(AUDIO_LENGTH);

    float *input_buffer = m_nn->getInputBuffer();

    if (!input_buffer)
    {
        delete reader;
        return false;
    }

    for (int i = 0; i < 99 * 43; i++)
    {
        input_buffer[i] = 0.0f;
    }

    m_audio_processor->get_spectrogram(reader, input_buffer);

    delete reader;

    float score = m_nn->predict();
    int command = m_nn->getLastCommandIndex();
    const char *label = m_nn->getLastCommandLabel();

    long end = millis();

    m_average_detect_time = (end - start) * 0.1f + m_average_detect_time * 0.9f;
    m_number_of_runs++;

    if (m_number_of_runs >= 100)
    {
        m_number_of_runs = 0;
        Serial.printf("[INFO] Avg detect time %.fms\n", m_average_detect_time);
    }

    Serial.printf("[PRED] label=%s index=%d score=%.2f\n", label, command, score);

    if (command == CMD_UNKNOWN || command == CMD_BACKGROUND || command < 0)
    {
        return false;
    }

    if (score < commandThreshold(command))
    {
        return false;
    }

    unsigned long now = millis();

    if (now - last_command_time < COMMAND_COOLDOWN_MS)
    {
        return false;
    }

    last_command_time = now;

    if (command == CMD_ON)
    {
        setLocalLed(255);

        if (m_speaker)
        {
            m_speaker->playOK();
        }

        // 給 Windows Python 用 COM10 讀取的關鍵訊號
        Serial.println("ON");

        Serial.printf("[ACTION] ON score=%.2f -> LED ON + SOUND OK + SERIAL ON\n", score);
        return true;
    }

    if (command == CMD_OFF)
    {
        setLocalLed(0);

        if (m_speaker)
        {
            m_speaker->playOK();
        }

        // 給 Windows Python 用 COM10 讀取的關鍵訊號
        Serial.println("OFF");

        Serial.printf("[ACTION] OFF score=%.2f -> LED OFF + SOUND OK + SERIAL OFF\n", score);
        return true;
    }

    if (command == CMD_ONE)
    {
        setLocalLed(80);

        Serial.printf("[ACTION] ONE score=%.2f -> LED LOW, no Windows trigger\n", score);
        return true;
    }

    if (command == CMD_TWO)
    {
        setLocalLed(160);

        Serial.printf("[ACTION] TWO score=%.2f -> LED MEDIUM, no Windows trigger\n", score);
        return true;
    }

    if (command == CMD_THREE)
    {
        setLocalLed(255);

        Serial.printf("[ACTION] THREE score=%.2f -> LED HIGH, no Windows trigger\n", score);
        return true;
    }

    return false;
}

void DetectWakeWordState::exitState()
{
    uint32_t free_ram = esp_get_free_heap_size();
    Serial.printf("Free ram before DetectWakeWord cleanup %d\n", free_ram);

    delete m_audio_processor;
    m_audio_processor = nullptr;

    delete m_nn;
    m_nn = nullptr;

    free_ram = esp_get_free_heap_size();
    Serial.printf("Free ram after DetectWakeWord cleanup %d\n", free_ram);
}