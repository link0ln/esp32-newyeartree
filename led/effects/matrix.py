# Matrix effect - direct buffer access
import time
import random
import micropython

NAME = "Matrix"
DESCRIPTION = "Matrix movie falling dots"

PARAMS = {
    'spawn_rate': {'name': 'Spawn Rate', 'type': 'int', 'min': 5, 'max': 40, 'default': 20},
    'fade_speed': {'name': 'Fade Speed', 'type': 'int', 'min': 10, 'max': 50, 'default': 20},
    'speed_min': {'name': 'Min Speed', 'type': 'int', 'min': 1, 'max': 3, 'default': 1},
    'speed_max': {'name': 'Max Speed', 'type': 'int', 'min': 2, 'max': 5, 'default': 3},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def fade_and_render(buf, leds, num, fade, factor):
    idx = 0
    for i in range(num):
        v = leds[i]
        if v > fade:
            v -= fade
        else:
            v = 0
        leds[i] = v
        gv = (v * factor) >> 8
        buf[idx] = 0       # R
        buf[idx + 1] = gv  # G - green only for matrix
        buf[idx + 2] = 0   # B
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    spawn_rate = get_param('spawn_rate')
    fade_speed = get_param('fade_speed')
    speed_min = get_param('speed_min')
    speed_max = get_param('speed_max')

    if num_leds > 100:
        speed_max = speed_max * num_leds // 50
        speed_min = speed_min * num_leds // 50

    leds_g = bytearray(num_leds)
    drops = []
    max_drops = num_leds // 20
    factor = int(brightness * 256 // 100)
    buf = strip.buf

    while True:
        if check_stop(session_id):
            return False

        if random.randint(0, 100) < spawn_rate and len(drops) < max_drops:
            drops.append([0, random.randint(speed_min, speed_max), random.randint(180, 255)])

        new_drops = []
        for d in drops:
            pos = int(d[0])
            if 0 <= pos < num_leds:
                leds_g[pos] = d[2]
            d[0] += d[1]
            if d[0] < num_leds + 5:
                new_drops.append(d)
        drops = new_drops

        fade_and_render(buf, leds_g, num_leds, fade_speed, factor)
        strip.write()
        time.sleep(0.03)

    return True
