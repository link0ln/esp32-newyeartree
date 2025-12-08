# Sparkle effect - direct buffer access
import time
import random
import micropython

NAME = "Sparkle"
DESCRIPTION = "Random glittering sparkles"

PARAMS = {
    'sparkle_count': {'name': 'Sparkle Count', 'type': 'int', 'min': 1, 'max': 10, 'default': 3},
    'fade_speed': {'name': 'Fade Speed', 'type': 'int', 'min': 10, 'max': 60, 'default': 25},
    'spawn_rate': {'name': 'Spawn Rate', 'type': 'int', 'min': 5, 'max': 30, 'default': 15},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def fade_and_render(buf, bright, num, fade, factor, bg_b):
    idx = 0
    for i in range(num):
        v = bright[i]
        if v > fade:
            v -= fade
        else:
            v = 0
        bright[i] = v
        if v > 0:
            lv = (v * factor) >> 8
            buf[idx] = lv
            buf[idx + 1] = lv
            buf[idx + 2] = lv
        else:
            buf[idx] = 0
            buf[idx + 1] = 0
            buf[idx + 2] = bg_b
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    sparkle_count = get_param('sparkle_count')
    fade_speed = get_param('fade_speed')
    spawn_rate = get_param('spawn_rate')

    factor = int(brightness * 256 // 100)
    bg_b = int(30 * brightness // 100)
    pixel_bright = bytearray(num_leds)
    buf = strip.buf

    while True:
        if check_stop(session_id):
            return False

        for _ in range(sparkle_count):
            if random.randint(0, 100) < spawn_rate:
                pixel_bright[random.randint(0, num_leds - 1)] = 255

        fade_and_render(buf, pixel_bright, num_leds, fade_speed, factor, bg_b)
        strip.write()
        time.sleep(0.02)

    return True
