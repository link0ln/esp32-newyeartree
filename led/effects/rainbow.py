# Rainbow effect
import time

NAME = "Rainbow"
DESCRIPTION = "Smooth rainbow wave"
DELAY = 0.02


def wheel(pos):
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))  # GRB


def run(strip, num_leds, brightness, session_id, check_stop):
    for j in range(256):
        if check_stop(session_id):
            return False
        for i in range(num_leds):
            pixel_index = (i * 256 // num_leds + j) & 255
            strip[i] = apply_brightness(wheel(pixel_index), brightness)
        strip.write()
        time.sleep(DELAY)
    return True
