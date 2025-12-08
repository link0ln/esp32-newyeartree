# Candle flicker effect
import time
import random

NAME = "Candle"
DESCRIPTION = "Realistic candle flicker"
DELAY = 0.03


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def run(strip, num_leds, brightness, session_id, check_stop):
    # Warm candle color (orange-yellow)
    base_hue = 25  # Orange

    for _ in range(200):
        if check_stop(session_id):
            return False

        # Random brightness flicker
        random_bright = random.randint(150, 255)
        random_delay = random.randint(10, 80)

        # Occasionally dim significantly (wind gust)
        if random.randint(0, 100) < 10:
            random_bright = random.randint(50, 120)

        # Warm color with slight variation
        r = random_bright
        g = int(random_bright * 0.4)  # Less green for warm color
        b = 0

        color = apply_brightness((r, g, b), brightness)

        for i in range(num_leds):
            # Add slight per-LED variation
            var = random.randint(-20, 20)
            pr = max(0, min(255, r + var))
            pg = max(0, min(255, g + var // 2))
            strip[i] = apply_brightness((pr, pg, 0), brightness)

        strip.write()
        time.sleep(random_delay / 1000.0)

    return True
