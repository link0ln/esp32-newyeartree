# Christmas effect - direct buffer access
import time
import random
import micropython

NAME = "Christmas"
DESCRIPTION = "Red and green with sparkle"

PARAMS = {
    'speed': {'name': 'Speed', 'type': 'int', 'min': 50, 'max': 200, 'default': 100},
    'sparkle_rate': {'name': 'Sparkle Rate', 'type': 'int', 'min': 0, 'max': 10, 'default': 2},
    'group_size': {'name': 'Group Size', 'type': 'int', 'min': 1, 'max': 10, 'default': 3},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def render_christmas(buf, num, offset, group_size, red_r, green_g):
    idx = 0
    for i in range(num):
        group = ((i + offset) // group_size) % 2
        if group == 0:
            buf[idx] = red_r
            buf[idx + 1] = 0
            buf[idx + 2] = 0
        else:
            buf[idx] = 0
            buf[idx + 1] = green_g
            buf[idx + 2] = 0
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    speed = get_param('speed')
    sparkle_rate = get_param('sparkle_rate')
    group_size = get_param('group_size')

    factor = int(brightness * 255 // 100)
    gold_g = int(180 * brightness // 100)
    gold_r = int(255 * brightness // 100)
    buf = strip.buf
    offset = 0

    frame = 0
    while True:
        if check_stop(session_id):
            return False

        render_christmas(buf, num_leds, offset, group_size, factor, factor)

        for i in range(num_leds):
            if random.randint(0, 100) < sparkle_rate:
                idx = i * 3
                buf[idx] = gold_r
                buf[idx + 1] = gold_g
                buf[idx + 2] = 0

        strip.write()
        time.sleep(speed / 1000.0)
        frame += 1
        if frame % 10 == 0:
            offset += 1
