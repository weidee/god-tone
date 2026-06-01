#include <Arduino.h>
#include "IndicatorLight.h"
#include "driver/uart.h"

void uart2_send(char *buf)
{
    while (*buf)
    {
        Serial2.write(*buf);
        vTaskDelay(2);
        buf++;
    }
}

void indicatorLedTask(void *param)
{
    IndicatorLight *indicator_light = static_cast<IndicatorLight *>(param);
    const TickType_t xMaxBlockTime = pdMS_TO_TICKS(100);

    while (true)
    {
        uint32_t ulNotificationValue = ulTaskNotifyTake(pdTRUE, xMaxBlockTime);

        if (ulNotificationValue > 0)
        {
            switch (indicator_light->getState())
            {
            case OFF:
                ledcWrite(0, 0);
                uart2_send((char *)"{8701fe}");
                break;

            case ON:
                ledcWrite(0, 255);
                uart2_send((char *)"{8701ff}");
                break;

            case PULSING:
            {
                while (indicator_light->getState() == PULSING)
                {
                    ledcWrite(0, 255);
                    uart2_send((char *)"{8701ff}");
                    vTaskDelay(250 / portTICK_PERIOD_MS);

                    if (indicator_light->getState() != PULSING)
                        break;

                    ledcWrite(0, 0);
                    uart2_send((char *)"{8701fe}");
                    vTaskDelay(250 / portTICK_PERIOD_MS);
                }

                ledcWrite(0, 0);
                uart2_send((char *)"{8701fe}");
                break;
            }
            }
        }
    }
}

IndicatorLight::IndicatorLight()
{
    Serial2.begin(115200, SERIAL_8N1, 15, 19);

    ledcSetup(0, 10000, 8);
    ledcAttachPin(2, 0);

    ledcWrite(0, 0);
    uart2_send((char *)"{8701fe}");

    m_state = OFF;

    xTaskCreate(indicatorLedTask, "Indicator LED Task", 4096, this, 1, &m_taskHandle);
}

void IndicatorLight::setState(IndicatorState state)
{
    m_state = state;
    xTaskNotify(m_taskHandle, 1, eSetBits);
}

IndicatorState IndicatorLight::getState()
{
    return m_state;
}