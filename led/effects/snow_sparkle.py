# Snow sparkle effect - white sparkles on colored background
import time
import random

NAME = "Snow Sparkle"
DESCRIPTION = "Sparkling snow effect"
DELAY = 0.02


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def run(strip, num_leds, brightness, session_id, check_stop):
    # Background color (dim blue for winter feel)
    bg_color = (16, 16, 64)

    # Sparkle color (bright white)
    sparkle_color = (255, 255, 255)

    for _ in range(400):
        if check_stop(session_id):
            return False

        # Set background
        for i in range(num_leds):
            strip[i] = apply_brightness(bg_color, brightness)

        # Add random sparkles
        num_sparkles = random.randint(1, max(1, num_leds // 10))
        sparkle_positions = []

        for _ in range(num_sparkles):
            pos = random.randint(0, num_leds - 1)
            sparkle_positions.append(pos)
            strip[pos] = apply_brightness(sparkle_color, brightness)

        strip.write()
        time.sleep(random.randint(20, 100) / 1000.0)

        # Turn off sparkles
        for pos in sparkle_positions:
            strip[pos] = apply_brightness(bg_color, brightness)

        strip.write()
        time.sleep(DELAY)

    return True
