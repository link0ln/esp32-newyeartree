# Meteor effect - direct buffer access
import time
import random
import micropython

NAME = "Meteor"
DESCRIPTION = "Falling meteor with glowing tail"

PARAMS = {
    'meteor_size': {'name': 'Meteor Size', 'type': 'int', 'min': 3, 'max': 15, 'default': 8},
    'trail_decay': {'name': 'Trail Decay', 'type': 'int', 'min': 30, 'max': 200, 'default': 64},
    'speed': {'name': 'Speed', 'type': 'int', 'min': 10, 'max': 80, 'default': 30},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def fade_trail(buf, num, decay):
    idx = 0
    for i in range(num):
        buf[idx] = (buf[idx] * decay) >> 8
        buf[idx + 1] = (buf[idx + 1] * decay) >> 8
        buf[idx + 2] = (buf[idx + 2] * decay) >> 8
        idx += 3


@micropython.native
def clear_buf(buf, num):
    for i in range(num * 3):
        buf[i] = 0


def run(strip, num_leds, brightness, session_id, check_stop):
    meteor_size = get_param('meteor_size')
    trail_decay = get_param('trail_decay')
    speed = get_param('speed')

    factor = brightness / 100.0
    step = 1 if num_leds < 200 else num_leds // 100
    if num_leds > 100:
        meteor_size = max(meteor_size, num_leds // 50)

    buf = strip.buf

    while True:
        if check_stop(session_id):
            return False

        clear_buf(buf, num_leds)

        for pos in range(0, num_leds + meteor_size, step):
            if check_stop(session_id):
                return False

            fade_trail(buf, num_leds, trail_decay)

            for j in range(meteor_size):
                idx_led = pos - j
                if 0 <= idx_led < num_leds:
                    scale = 255 - (255 * j // meteor_size)
                    idx = idx_led * 3
                    buf[idx] = int(200 * scale * factor // 255)
                    buf[idx + 1] = int(200 * scale * factor // 255)
                    buf[idx + 2] = int(255 * scale * factor // 255)

            strip.write()
            time.sleep(speed / 1000.0)

    return True
