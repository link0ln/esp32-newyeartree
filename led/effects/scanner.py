# Scanner effect - direct buffer access
import time
import micropython

NAME = "Scanner"
DESCRIPTION = "Knight Rider scanner"

PARAMS = {
    'eye_size': {'name': 'Eye Size', 'type': 'int', 'min': 2, 'max': 10, 'default': 4},
    'fade_amount': {'name': 'Fade Amount', 'type': 'int', 'min': 50, 'max': 200, 'default': 96},
    'speed': {'name': 'Speed', 'type': 'int', 'min': 10, 'max': 60, 'default': 30},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def fade_buffer(buf, num, amount):
    idx = 0
    for i in range(num):
        buf[idx] = (buf[idx] * amount) >> 8
        buf[idx + 1] = (buf[idx + 1] * amount) >> 8
        buf[idx + 2] = (buf[idx + 2] * amount) >> 8
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    eye_size = get_param('eye_size')
    fade_amount = get_param('fade_amount')
    speed = get_param('speed')

    step = 1 if num_leds < 200 else num_leds // 100
    if num_leds > 100:
        eye_size = max(eye_size, num_leds // 50)

    full_r = int(255 * brightness // 100)
    half_r = int(127 * brightness // 100)
    buf = strip.buf

    while True:
        if check_stop(session_id):
            return False

        for pos in range(0, num_leds - eye_size, step):
            if check_stop(session_id):
                return False
            fade_buffer(buf, num_leds, fade_amount)
            mid = eye_size // 2
            for j in range(eye_size):
                idx = (pos + j) * 3
                if pos + j < num_leds:
                    rv = full_r if j == mid else half_r
                    buf[idx] = rv
                    buf[idx + 1] = 0
                    buf[idx + 2] = 0
            strip.write()
            time.sleep(speed / 1000.0)

        for pos in range(num_leds - eye_size - 1, -1, -step):
            if check_stop(session_id):
                return False
            fade_buffer(buf, num_leds, fade_amount)
            mid = eye_size // 2
            for j in range(eye_size):
                idx = (pos + j) * 3
                if pos + j < num_leds:
                    rv = full_r if j == mid else half_r
                    buf[idx] = rv
                    buf[idx + 1] = 0
                    buf[idx + 2] = 0
            strip.write()
            time.sleep(speed / 1000.0)

    return True
