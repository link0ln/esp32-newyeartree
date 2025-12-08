# Snow sparkle - direct buffer access
import time
import random
import micropython

NAME = "Snow Sparkle"
DESCRIPTION = "Sparkling snow effect"

PARAMS = {
    'bg_blue': {'name': 'Background Blue', 'type': 'int', 'min': 0, 'max': 100, 'default': 64},
    'sparkle_min': {'name': 'Min Sparkles', 'type': 'int', 'min': 1, 'max': 5, 'default': 1},
    'sparkle_max': {'name': 'Max Sparkles', 'type': 'int', 'min': 2, 'max': 10, 'default': 5},
    'delay_min': {'name': 'Min Delay (ms)', 'type': 'int', 'min': 10, 'max': 80, 'default': 20},
    'delay_max': {'name': 'Max Delay (ms)', 'type': 'int', 'min': 50, 'max': 150, 'default': 100},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def fill_bg(buf, num, bg_r, bg_g, bg_b):
    idx = 0
    for i in range(num):
        buf[idx] = bg_r
        buf[idx + 1] = bg_g
        buf[idx + 2] = bg_b
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    bg_blue = get_param('bg_blue')
    sparkle_min = get_param('sparkle_min')
    sparkle_max = get_param('sparkle_max')
    delay_min = get_param('delay_min')
    delay_max = get_param('delay_max')

    factor = brightness / 100.0
    bg_g = int(16 * factor)
    bg_r = int(16 * factor)
    bg_b = int(bg_blue * factor)
    sparkle_v = int(255 * factor)
    buf = strip.buf

    while True:
        if check_stop(session_id):
            return False

        fill_bg(buf, num_leds, bg_r, bg_g, bg_b)

        sparkle_positions = []
        for _ in range(random.randint(sparkle_min, sparkle_max)):
            pos = random.randint(0, num_leds - 1)
            sparkle_positions.append(pos)
            idx = pos * 3
            buf[idx] = sparkle_v
            buf[idx + 1] = sparkle_v
            buf[idx + 2] = sparkle_v

        strip.write()
        time.sleep(random.randint(delay_min, delay_max) / 1000.0)

        for pos in sparkle_positions:
            idx = pos * 3
            buf[idx] = bg_r
            buf[idx + 1] = bg_g
            buf[idx + 2] = bg_b

        strip.write()
        time.sleep(0.02)

    return True
