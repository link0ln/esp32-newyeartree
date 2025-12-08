# Theater chase - direct buffer access
import time
import micropython

NAME = "Theater Chase"
DESCRIPTION = "Classic marquee lights"

PARAMS = {
    'speed': {'name': 'Speed', 'type': 'int', 'min': 30, 'max': 150, 'default': 80},
    'spacing': {'name': 'Spacing', 'type': 'int', 'min': 2, 'max': 6, 'default': 3},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def render_theater(buf, num, q, spacing, r, g, b):
    for i in range(num * 3):
        buf[i] = 0
    i = 0
    while i < num:
        idx_led = i + q
        if idx_led < num:
            idx = idx_led * 3
            buf[idx] = r
            buf[idx + 1] = g
            buf[idx + 2] = b
        i += spacing


def run(strip, num_leds, brightness, session_id, check_stop):
    speed = get_param('speed')
    spacing = get_param('spacing')

    factor = brightness / 100.0
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 255, 255)]
    buf = strip.buf

    while True:
        for color in colors:
            if check_stop(session_id):
                return False

            r = int(color[0] * factor)
            g = int(color[1] * factor)
            b = int(color[2] * factor)

            for _ in range(10):
                for q in range(spacing):
                    if check_stop(session_id):
                        return False
                    render_theater(buf, num_leds, q, spacing, r, g, b)
                    strip.write()
                    time.sleep(speed / 1000.0)
