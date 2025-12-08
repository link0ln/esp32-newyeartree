# Running lights effect - sine wave brightness
import time
import math

NAME = "Running"
DESCRIPTION = "Running lights wave"
DELAY = 0.03


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def run(strip, num_leds, brightness, session_id, check_stop):
    # Running color (warm white/gold for christmas)
    base_r = 255
    base_g = 200
    base_b = 50

    position = 0

    for _ in range(300):
        if check_stop(session_id):
            return False

        position += 1

        for i in range(num_leds):
            # Sine wave creates smooth running pattern
            level = ((math.sin((i + position) * 0.3) + 1) * 127)
            level = int(level)

            r = int((level / 255) * base_r)
            g = int((level / 255) * base_g)
            b = int((level / 255) * base_b)

            strip[i] = apply_brightness((r, g, b), brightness)

        strip.write()
        time.sleep(DELAY)

    return True
