# Fire effect - direct buffer access
import time
import random
import micropython

NAME = "Fire"
DESCRIPTION = "Realistic fire flame"

PARAMS = {
    'cooling': {'name': 'Cooling', 'type': 'int', 'min': 20, 'max': 100, 'default': 55},
    'sparking': {'name': 'Sparking', 'type': 'int', 'min': 50, 'max': 200, 'default': 120},
    'speed': {'name': 'Speed', 'type': 'int', 'min': 10, 'max': 80, 'default': 30},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def process_fire(buf, heat, num, cool_base, factor):
    # Cool down
    for i in range(num):
        cooldown = (i * 7 + heat[i]) % (cool_base + 1)
        if heat[i] > cooldown:
            heat[i] -= cooldown
        else:
            heat[i] = 0

    # Heat rises
    for i in range(num - 1, 1, -1):
        heat[i] = (heat[i - 1] + heat[i - 2] + heat[i - 2]) // 3

    # Render to buffer
    idx = 0
    for i in range(num):
        t = heat[i]
        if t < 85:
            r = t * 3
            g = 0
            b = 0
        elif t < 170:
            r = 255
            g = (t - 85) * 3
            b = 0
        else:
            r = 255
            g = 255
            b = (t - 170) * 3
        buf[idx] = (r * factor) >> 8
        buf[idx + 1] = (g * factor) >> 8
        buf[idx + 2] = (b * factor) >> 8
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    cooling = get_param('cooling')
    sparking = get_param('sparking')
    speed = get_param('speed')

    heat = bytearray(num_leds)
    spark_zone = min(7, num_leds - 1)
    if num_leds > 100:
        spark_zone = num_leds // 50
        sparking = min(255, sparking * 2)

    factor = int(brightness * 256 // 100)
    cool_base = ((cooling * 10) // num_leds) + 2
    buf = strip.buf

    while True:
        if check_stop(session_id):
            return False

        # Spark
        if random.randint(0, 255) < sparking:
            y = random.randint(0, spark_zone)
            heat[y] = min(255, heat[y] + random.randint(160, 255))

        process_fire(buf, heat, num_leds, cool_base, factor)
        strip.write()
        time.sleep(speed / 1000.0)

    return True
