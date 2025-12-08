# Bouncing balls - direct buffer access
import time
import random
import micropython

NAME = "Bouncing"
DESCRIPTION = "Bouncing balls with gravity"

PARAMS = {
    'num_balls': {'name': 'Ball Count', 'type': 'int', 'min': 1, 'max': 6, 'default': 3},
    'gravity': {'name': 'Gravity', 'type': 'float', 'min': 0.2, 'max': 1.0, 'default': 0.5},
    'speed': {'name': 'Speed', 'type': 'int', 'min': 10, 'max': 40, 'default': 20},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def clear_buf(buf, num):
    for i in range(num * 3):
        buf[i] = 0


def run(strip, num_leds, brightness, session_id, check_stop):
    num_balls = get_param('num_balls')
    gravity = -get_param('gravity')
    speed = get_param('speed')

    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    factor = brightness / 100.0

    if num_leds > 100:
        num_balls = max(num_balls, num_leds // 100)
        gravity = gravity * (num_leds / 50)

    balls = []
    for i in range(num_balls):
        c = colors[i % len(colors)]
        balls.append([1.0, 2.5 + (num_leds / 200), 0, 0, 0.9 - (i * 0.05),
                      int(c[0] * factor), int(c[1] * factor), int(c[2] * factor)])

    buf = strip.buf

    while True:
        if check_stop(session_id):
            return False

        clear_buf(buf, num_leds)

        for b in balls:
            b[3] += 1
            b[0] = 0.5 * gravity * (b[3] ** 2) + b[1] * b[3]

            if b[0] < 0:
                b[0] = 0
                b[1] = b[4] * b[1]
                b[3] = 0
                if b[1] < 0.5:
                    b[1] = 2.0 + random.random() + (num_leds / 200)
                    b[4] = 0.85 + random.random() * 0.1

            b[2] = int(b[0] * (num_leds - 1))
            if b[2] >= num_leds:
                b[2] = num_leds - 1

            idx = b[2] * 3
            buf[idx] = b[5]      # R
            buf[idx + 1] = b[6]  # G
            buf[idx + 2] = b[7]  # B

        strip.write()
        time.sleep(speed / 1000.0)

    return True
