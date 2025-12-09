# Colorful trains effect - direct buffer access
import time
import random
import micropython

NAME = "Trains"
DESCRIPTION = "Colorful moving trains"

PARAMS = {
    'p1_count': {'name': 'Train Count', 'type': 'int', 'min': 2, 'max': 10, 'default': 5},
    'p2_speed_min': {'name': 'Min Speed', 'type': 'float', 'min': 0.01, 'max': 2.0, 'default': 0.3},
    'p3_speed_max': {'name': 'Max Speed', 'type': 'float', 'min': 0.5, 'max': 6.0, 'default': 2.0},
    'p4_len_min': {'name': 'Min Length', 'type': 'int', 'min': 1, 'max': 15, 'default': 3},
    'p5_len_max': {'name': 'Max Length', 'type': 'int', 'min': 3, 'max': 40, 'default': 15},
    'p6_trail': {'name': 'Trail Length', 'type': 'int', 'min': 0, 'max': 30, 'default': 10},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def render_trains(buf, num, trains, factor, trail_len):
    # Clear buffer
    for i in range(num * 3):
        buf[i] = 0

    # Render each train with color mixing
    for train in trains:
        pos = int(train[0])
        length = train[1]
        direction = train[6]
        r, g, b = train[3], train[4], train[5]

        # Draw trail (fading behind train)
        if trail_len > 0 and trail_len < 255:
            for i in range(int(trail_len)):
                # Trail is behind the train (opposite to direction)
                if direction > 0:
                    led_pos = pos - length - i
                else:
                    led_pos = pos + length + i

                # Wrap around
                while led_pos >= num:
                    led_pos -= num
                while led_pos < 0:
                    led_pos += num

                # Fade factor for trail
                fade = (trail_len - i) * 255 // (trail_len + 1)
                idx = led_pos * 3
                nr = buf[idx] + ((r * fade * factor) >> 16)
                ng = buf[idx + 1] + ((g * fade * factor) >> 16)
                nb = buf[idx + 2] + ((b * fade * factor) >> 16)
                buf[idx] = nr if nr < 255 else 255
                buf[idx + 1] = ng if ng < 255 else 255
                buf[idx + 2] = nb if nb < 255 else 255

        # Draw train body
        for i in range(length):
            led_pos = pos + i * (-1 if direction > 0 else 1)
            # Wrap around
            while led_pos >= num:
                led_pos -= num
            while led_pos < 0:
                led_pos += num

            idx = led_pos * 3
            # Add colors (mix when overlapping)
            nr = buf[idx] + ((r * factor) >> 8)
            ng = buf[idx + 1] + ((g * factor) >> 8)
            nb = buf[idx + 2] + ((b * factor) >> 8)
            buf[idx] = nr if nr < 255 else 255
            buf[idx + 1] = ng if ng < 255 else 255
            buf[idx + 2] = nb if nb < 255 else 255


def run(strip, num_leds, brightness, session_id, check_stop):
    num_trains = get_param('p1_count')
    speed_min = get_param('p2_speed_min')
    speed_max = get_param('p3_speed_max')
    len_min = get_param('p4_len_min')
    len_max = get_param('p5_len_max')
    trail_len = get_param('p6_trail')

    # Scale speeds for large strips
    if num_leds > 100:
        scale = num_leds / 100
        speed_min = speed_min * scale
        speed_max = speed_max * scale

    factor = int(brightness * 256 // 100)
    buf = strip.buf

    # Train colors (bright, saturated)
    colors = [
        (255, 0, 0),     # Red
        (0, 255, 0),     # Green
        (0, 0, 255),     # Blue
        (255, 255, 0),   # Yellow
        (255, 0, 255),   # Magenta
        (0, 255, 255),   # Cyan
        (255, 128, 0),   # Orange
        (128, 0, 255),   # Purple
    ]

    # Create trains: [position, length, speed, r, g, b, direction, distance]
    # distance tracks how far train has traveled
    trains = []
    for i in range(num_trains):
        pos = random.randint(0, num_leds - 1)
        length = random.randint(len_min, len_max)
        speed = random.uniform(speed_min, speed_max)
        color = colors[i % len(colors)]
        direction = 1 if random.random() > 0.5 else -1
        trains.append([float(pos), length, speed, color[0], color[1], color[2], direction, 0.0])

    while True:
        if check_stop(session_id):
            return False

        # Update train positions
        for i, train in enumerate(trains):
            train[0] += train[2] * train[6]  # pos += speed * direction
            train[7] += train[2]  # track distance traveled

            # Wrap around
            if train[0] >= num_leds:
                train[0] -= num_leds
            elif train[0] < 0:
                train[0] += num_leds

            # Respawn train after it travels full strip length
            if train[7] >= num_leds:
                new_dir = 1 if random.random() > 0.5 else -1
                new_pos = 0 if new_dir > 0 else num_leds - 1
                new_len = random.randint(len_min, len_max)
                new_speed = random.uniform(speed_min, speed_max)
                new_color = colors[random.randint(0, len(colors) - 1)]
                trains[i] = [float(new_pos), new_len, new_speed, new_color[0], new_color[1], new_color[2], new_dir, 0.0]

        render_trains(buf, num_leds, trains, factor, trail_len)
        strip.write()
        time.sleep(0.02)
