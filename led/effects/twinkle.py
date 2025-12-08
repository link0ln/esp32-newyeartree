# Twinkle stars effect
import time
import random

NAME = "Twinkle Stars"
DESCRIPTION = "Random twinkling stars"
DELAY = 0.05
NUM_STARS = 5
FADE_SPEED = 15


def run(strip, num_leds, brightness, session_id, check_stop):
    colors = [
        (255, 200, 100), (200, 220, 255), (255, 180, 0),
        (180, 180, 200), (255, 0, 0), (0, 255, 0)
    ]

    star_brightness = [0] * num_leds
    star_colors = [(0, 0, 0)] * num_leds
    star_direction = [0] * num_leds

    for _ in range(100):
        if check_stop(session_id):
            return False

        for _ in range(NUM_STARS):
            if random.random() < 0.1:
                pos = random.randint(0, num_leds - 1)
                if star_brightness[pos] == 0:
                    star_colors[pos] = random.choice(colors)
                    star_direction[pos] = 1

        for i in range(num_leds):
            if star_direction[i] == 1:
                star_brightness[i] += FADE_SPEED
                if star_brightness[i] >= 100:
                    star_brightness[i] = 100
                    star_direction[i] = -1
            elif star_direction[i] == -1:
                star_brightness[i] -= FADE_SPEED
                if star_brightness[i] <= 0:
                    star_brightness[i] = 0
                    star_direction[i] = 0

            if star_brightness[i] > 0:
                r, g, b = star_colors[i]
                factor = (star_brightness[i] / 100.0) * (brightness / 100.0)
                strip[i] = (int(g * factor), int(r * factor), int(b * factor))
            else:
                strip[i] = (0, 0, 0)

        strip.write()
        time.sleep(DELAY)
    return True
