# Running lights - direct buffer access
import time
import micropython

NAME = "Running"
DESCRIPTION = "Running lights wave"

PARAMS = {
    'speed': {'name': 'Speed', 'type': 'int', 'min': 15, 'max': 60, 'default': 30},
    'wave_size': {'name': 'Wave Size', 'type': 'float', 'min': 0.1, 'max': 0.6, 'default': 0.3},
}
settings = {}

_sine = None


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


def get_sine():
    global _sine
    if _sine is None:
        import math
        _sine = bytearray(256)
        for i in range(256):
            _sine[i] = int((math.sin(i * 3.14159 * 2 / 256) + 1) * 127)
    return _sine


@micropython.native
def render_running(buf, sine, num, pos, wave_mult, factor, br, bg, bb):
    idx = 0
    for i in range(num):
        sine_idx = ((i + pos) * wave_mult) >> 8
        level = sine[sine_idx & 255]
        buf[idx] = (level * br * factor) >> 16
        buf[idx + 1] = (level * bg * factor) >> 16
        buf[idx + 2] = (level * bb * factor) >> 16
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    speed = get_param('speed')
    wave_size = get_param('wave_size')

    sine = get_sine()
    factor = int(brightness * 256 // 100)
    wave_mult = int(wave_size * 256)
    br, bg, bb = 255, 200, 50
    buf = strip.buf
    position = 0

    while True:
        if check_stop(session_id):
            return False
        position += 1
        render_running(buf, sine, num_leds, position, wave_mult, factor, br, bg, bb)
        strip.write()
        time.sleep(speed / 1000.0)

    return True
