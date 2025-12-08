# Color bounce effect - bouncing LED with fade trail
import time

NAME = "Color Bounce"
DESCRIPTION = "Bouncing LED with trail"
DELAY = 0.03


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def run(strip, num_leds, brightness, session_id, check_stop):
    # Colors to cycle through
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
    ]

    color_idx = 0
    position = 0
    direction = 1

    # Trail buffer
    leds = [(0, 0, 0)] * num_leds

    for _ in range(300):
        if check_stop(session_id):
            return False

        # Fade all LEDs
        new_leds = []
        for r, g, b in leds:
            new_leds.append((
                max(0, r - 30),
                max(0, g - 30),
                max(0, b - 30)
            ))
        leds = new_leds

        # Set current position to full color
        color = colors[color_idx]
        leds[position] = color

        # Write to strip
        for i in range(num_leds):
            strip[i] = apply_brightness(leds[i], brightness)
        strip.write()

        # Move position
        position += direction
        if position >= num_leds - 1:
            position = num_leds - 1
            direction = -1
            color_idx = (color_idx + 1) % len(colors)
        elif position <= 0:
            position = 0
            direction = 1
            color_idx = (color_idx + 1) % len(colors)

        time.sleep(DELAY)

    return True
