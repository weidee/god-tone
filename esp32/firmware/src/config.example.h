// Copy this file to config.h and fill in local values before building.

// WiFi credentials
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PSWD "YOUR_WIFI_PASSWORD"

// Are you using an I2S microphone? Comment this out to use analog mic input.
#define USE_I2S_MIC_INPUT

// I2S microphone settings
#define I2S_MIC_CHANNEL I2S_CHANNEL_FMT_ONLY_LEFT
// #define I2S_MIC_CHANNEL I2S_CHANNEL_FMT_ONLY_RIGHT
#define I2S_MIC_SERIAL_CLOCK GPIO_NUM_33
#define I2S_MIC_LEFT_RIGHT_CLOCK GPIO_NUM_26
#define I2S_MIC_SERIAL_DATA GPIO_NUM_25

// Analog microphone settings - ADC1_CHANNEL_7 is GPIO35
#define ADC_MIC_CHANNEL ADC1_CHANNEL_7

// Speaker settings
#define I2S_SPEAKER_SERIAL_CLOCK GPIO_NUM_14
#define I2S_SPEAKER_LEFT_RIGHT_CLOCK GPIO_NUM_12
#define I2S_SPEAKER_SERIAL_DATA GPIO_NUM_27

// Command recognition settings.
// This project currently handles ON/OFF locally from the embedded model, but
// the legacy Wit.ai recognizer code still references this macro.
#define COMMAND_RECOGNITION_ACCESS_KEY "YOUR_WIT_AI_ACCESS_KEY"
