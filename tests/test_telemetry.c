#include "Telemetry.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_on_state_contains_measured_output(void)
{
    char buffer[TELEMETRY_BUFFER_SIZE];

    Telemetry_Format(buffer, 5.24f, 0.129f, 5.18f, 0.129f,
                     1290, 0.675f, 10.0f, 1);

    assert(strstr(buffer, "V:5.24, I:129") != NULL);
    assert(strstr(buffer, "OUT_V:5.18, OUT_I:129") != NULL);
    assert(strstr(buffer, "RLY:ON") != NULL);
}

static void test_off_state_contains_zero_output(void)
{
    char buffer[TELEMETRY_BUFFER_SIZE];

    Telemetry_Format(buffer, 5.24f, 0.002f, 0.0f, 0.0f,
                     20, 0.010f, 1.0f, 0);

    assert(strstr(buffer, "OUT_V:0.00, OUT_I:0") != NULL);
    assert(strstr(buffer, "RLY:OFF") != NULL);
}

int main(void)
{
    test_on_state_contains_measured_output();
    test_off_state_contains_zero_output();
    puts("telemetry tests passed");
    return 0;
}
