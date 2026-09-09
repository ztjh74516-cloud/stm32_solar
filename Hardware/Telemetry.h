#ifndef __TELEMETRY_H
#define __TELEMETRY_H

#include <stdint.h>

#define TELEMETRY_BUFFER_SIZE 128

void Telemetry_Format(char *buffer,
                      float pv_voltage,
                      float pv_current,
                      float output_voltage,
                      float output_current,
                      int16_t shunt_raw,
                      float pv_power,
                      float threshold_voltage,
                      uint8_t relay_status);

#endif
