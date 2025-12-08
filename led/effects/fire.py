# Fire effect - realistic flame simulation
import time
import random

NAME = "Fire"
DESCRIPTION = "Realistic fire flame"
DELAY = 0.03
COOLING = 55
SPARKING = 120


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def heat_color(temperature):
    """Convert heat value (0-255) to RGB color"""
    if temperature < 85:
        return (temperature * 3, 0, 0)
    elif temperature < 170:
        return (255, (temperature - 85) * 3, 0)
    else:
        return (255, 255, (temperature - 170) * 3)


def run(strip, num_leds, brightness, session_id, check_stop):
    heat = [0] * num_leds

    for _ in range(200):
        if check_stop(session_id):
            return False

        # Cool down
        for i in range(num_leds):
            cooldown = random.randint(0, ((COOLING * 10) // num_leds) + 2)
            heat[i] = max(0, heat[i] - cooldown)

        # Heat rises and diffuses
        for i in range(num_leds - 1, 1, -1):
            heat[i] = (heat[i - 1] + heat[i - 2] + heat[i - 2]) // 3

        # Random sparks at bottom
        if random.randint(0, 255) < SPARKING:
            y = random.randint(0, min(7, num_leds - 1))
            heat[y] = min(255, heat[y] + random.randint(160, 255))

        # Map heat to colors
        for i in range(num_leds):
            color = heat_color(heat[i])
            strip[i] = apply_brightness(color, brightness)

        strip.write()
        time.sleep(DELAY)

    return True
