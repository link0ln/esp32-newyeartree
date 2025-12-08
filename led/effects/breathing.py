# Breathing effect - direct buffer access
import time
import micropython

NAME = "Breathing"
DESCRIPTION = "Smooth breathing pulse"

PARAMS = {
    'speed': {'name': 'Speed', 'type': 'int', 'min': 10, 'max': 50, 'default': 20},
    'step': {'name': 'Step Size', 'type': 'int', 'min': 1, 'max': 10, 'default': 2},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def fill_buf(buf, num, r, g, b):
    idx = 0
    for i in range(num):
        buf[idx] = r
        buf[idx + 1] = g
        buf[idx + 2] = b
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    speed = get_param('speed')
    step = get_param('step')

    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 255), (0, 255, 255)]
    factor = brightness / 100.0
    buf = strip.buf

    while True:
        for color in colors:
            if check_stop(session_id):
                return False

            for level in range(0, 101, step):
                if check_stop(session_id):
                    return False
                f = (level / 100.0) * factor
                fill_buf(buf, num_leds, int(color[0] * f), int(color[1] * f), int(color[2] * f))
                strip.write()
                time.sleep(speed / 1000.0)

            for level in range(100, -1, -step):
                if check_stop(session_id):
                    return False
                f = (level / 100.0) * factor
                fill_buf(buf, num_leds, int(color[0] * f), int(color[1] * f), int(color[2] * f))
                strip.write()
                time.sleep(speed / 1000.0)
