# Larson Scanner effect - Knight Rider / Cylon eye
import time

NAME = "Scanner"
DESCRIPTION = "Knight Rider scanner"
DELAY = 0.03
EYE_SIZE = 4
FADE_AMOUNT = 96


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def fade_all(strip, num_leds, amount):
    """Fade all pixels"""
    for i in range(num_leds):
        g, r, b = strip[i]
        r = (r * amount) // 256
        g = (g * amount) // 256
        b = (b * amount) // 256
        strip[i] = (g, r, b)


def run(strip, num_leds, brightness, session_id, check_stop):
    color = (255, 0, 0)  # Red like Knight Rider

    for _ in range(6):  # 6 back-and-forth cycles
        if check_stop(session_id):
            return False

        # Forward
        for pos in range(num_leds - EYE_SIZE):
            if check_stop(session_id):
                return False

            fade_all(strip, num_leds, FADE_AMOUNT)

            # Draw the eye
            for j in range(EYE_SIZE):
                idx = pos + j
                if idx < num_leds:
                    # Brightest in center
                    if j == EYE_SIZE // 2:
                        strip[idx] = apply_brightness(color, brightness)
                    else:
                        r = color[0] // 2
                        g = color[1] // 2
                        b = color[2] // 2
                        strip[idx] = apply_brightness((r, g, b), brightness)

            strip.write()
            time.sleep(DELAY)

        # Backward
        for pos in range(num_leds - EYE_SIZE - 1, -1, -1):
            if check_stop(session_id):
                return False

            fade_all(strip, num_leds, FADE_AMOUNT)

            for j in range(EYE_SIZE):
                idx = pos + j
                if idx < num_leds:
                    if j == EYE_SIZE // 2:
                        strip[idx] = apply_brightness(color, brightness)
                    else:
                        r = color[0] // 2
                        g = color[1] // 2
                        b = color[2] // 2
                        strip[idx] = apply_brightness((r, g, b), brightness)

            strip.write()
            time.sleep(DELAY)

    return True
