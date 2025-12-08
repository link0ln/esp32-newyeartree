# Wave effect - direct buffer access
import time
import micropython

NAME = "Color Wave"
DESCRIPTION = "Flowing wave of colors"

PARAMS = {
    'speed': {'name': 'Speed', 'type': 'int', 'min': 10, 'max': 60, 'default': 30},
    'wave_length': {'name': 'Wave Length', 'type': 'int', 'min': 128, 'max': 512, 'default': 256},
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
            _sine[i] = int((math.sin(i * 3.14159 * 2 / 256) + 1) * 127.5)
    return _sine


@micropython.native
def render_wave(buf, sine, num, offset, cr, cg, cb, factor):
    idx = 0
    for i in range(num):
        wave_pos = ((i * 256 // num) + offset) & 255
        wave_val = sine[wave_pos]
        buf[idx] = (cr * wave_val * factor) >> 16
        buf[idx + 1] = (cg * wave_val * factor) >> 16
        buf[idx + 2] = (cb * wave_val * factor) >> 16
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    speed = get_param('speed')
    wave_length = get_param('wave_length')

    sine = get_sine()
    factor = int(brightness * 256 // 100)
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 128, 0)]
    buf = strip.buf

    while True:
        for cr, cg, cb in colors:
            if check_stop(session_id):
                return False
            for offset in range(wave_length):
                if check_stop(session_id):
                    return False
                render_wave(buf, sine, num_leds, offset, cr, cg, cb, factor)
                strip.write()
                time.sleep(speed / 1000.0)
