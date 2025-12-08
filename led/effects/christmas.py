# Christmas colors effect
import time
import random

NAME = "Christmas"
DESCRIPTION = "Red and green with sparkle"
DELAY = 0.1


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def run(strip, num_leds, brightness, session_id, check_stop):
    red = (255, 0, 0)
    green = (0, 255, 0)
    gold = (255, 180, 0)
    offset = 0

    for frame in range(60):
        if check_stop(session_id):
            return False

        for i in range(num_leds):
            group = ((i + offset) // 3) % 2
            color = red if group == 0 else green
            if random.random() < 0.02:
                color = gold
            strip[i] = apply_brightness(color, brightness)

        strip.write()
        time.sleep(DELAY)
        if frame % 10 == 0:
            offset += 1
    return True
