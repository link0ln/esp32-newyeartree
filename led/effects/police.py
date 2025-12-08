# Police effect - direct buffer access
import time
import micropython

NAME = "Police"
DESCRIPTION = "Red and blue police lights"

PARAMS = {
    'flash_speed': {'name': 'Flash Speed', 'type': 'int', 'min': 20, 'max': 100, 'default': 50},
    'flashes': {'name': 'Flash Count', 'type': 'int', 'min': 1, 'max': 6, 'default': 3},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def fill_half(buf, half, num, r1, b2):
    idx = 0
    for i in range(half):
        buf[idx] = r1
        buf[idx + 1] = 0
        buf[idx + 2] = 0
        idx += 3
    for i in range(half, num):
        buf[idx] = 0
        buf[idx + 1] = 0
        buf[idx + 2] = b2
        idx += 3


@micropython.native
def clear_buf(buf, num):
    for i in range(num * 3):
        buf[i] = 0


def run(strip, num_leds, brightness, session_id, check_stop):
    flash_speed = get_param('flash_speed')
    flashes = get_param('flashes')

    factor = int(255 * brightness // 100)
    half = num_leds // 2
    buf = strip.buf

    while True:
        if check_stop(session_id):
            return False

        for _ in range(flashes):
            if check_stop(session_id):
                return False
            fill_half(buf, half, num_leds, factor, 0)
            strip.write()
            time.sleep(flash_speed / 1000.0)
            clear_buf(buf, num_leds)
            strip.write()
            time.sleep(flash_speed / 1000.0)

        for _ in range(flashes):
            if check_stop(session_id):
                return False
            fill_half(buf, half, num_leds, 0, factor)
            strip.write()
            time.sleep(flash_speed / 1000.0)
            clear_buf(buf, num_leds)
            strip.write()
            time.sleep(flash_speed / 1000.0)

    return True
