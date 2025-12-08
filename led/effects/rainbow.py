# Rainbow effect - direct buffer access
import time
import micropython

NAME = "Rainbow"
DESCRIPTION = "Smooth rainbow wave"

PARAMS = {
    'speed': {'name': 'Speed', 'type': 'int', 'min': 10, 'max': 50, 'default': 20},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def render_rainbow(buf, num, offset, factor):
    idx = 0
    for i in range(num):
        pos = ((i * 256 // num) + offset) & 255
        if pos < 85:
            r = pos * 3
            g = 255 - pos * 3
            b = 0
        elif pos < 170:
            pos2 = pos - 85
            r = 255 - pos2 * 3
            g = 0
            b = pos2 * 3
        else:
            pos2 = pos - 170
            r = 0
            g = pos2 * 3
            b = 255 - pos2 * 3
        buf[idx] = (r * factor) >> 8
        buf[idx + 1] = (g * factor) >> 8
        buf[idx + 2] = (b * factor) >> 8
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    speed = get_param('speed')
    delay = speed / 1000.0
    factor = int(brightness * 256 // 100)
    step = 1 if num_leds < 200 else 2
    buf = strip.buf

    while True:
        for j in range(0, 256, step):
            if check_stop(session_id):
                return False
            render_rainbow(buf, num_leds, j, factor)
            strip.write()
            time.sleep(delay)
