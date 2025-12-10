# UDP LED Control Mode
# Minimal code for maximum performance
#
# Protocol (port 5000):
#   - N*5 bytes: LED updates (idx_lo, idx_hi, G, R, B) x N
#   - 1 byte 0xFF: Exit UDP mode and reboot
#
# Buffer architecture:
#   - Thread 1: UDP receiver -> updates buffer
#   - Thread 2: Continuously writes buffer to LED strip

import gc
import machine
import neopixel
import socket
import os
import _thread
import time

NUM_LEDS = 700
LED_PIN = 3  # LED strip pin (pin 8 is onboard status LED)
UDP_PORT = 5000

# Pre-allocated buffer (GRB format for WS2815)
buffer = bytearray(NUM_LEDS * 3)
strip = None
running = True
new_data = True  # Flag to avoid unnecessary writes


def led_writer():
    """Thread: continuously write buffer to strip at max speed"""
    global strip, running, new_data

    buf = memoryview(buffer)

    while running:
        if new_data and strip:
            new_data = False
            s = strip  # Local reference for speed
            for i in range(NUM_LEDS):
                j = i * 3
                s[i] = (buf[j], buf[j+1], buf[j+2])
            s.write()
        else:
            time.sleep_ms(1)


def clear_flag():
    """Remove UDP mode flag file"""
    try:
        os.remove('/udp_mode')
    except:
        pass


def run():
    """Main UDP receiver loop"""
    global strip, running, new_data

    print("[UDP] Starting UDP LED mode...")
    gc.collect()

    # Initialize LED strip
    strip = neopixel.NeoPixel(machine.Pin(LED_PIN), NUM_LEDS)

    # Clear all LEDs and buffer
    for i in range(NUM_LEDS):
        strip[i] = (0, 0, 0)
    strip.write()

    # Status LED (first pixel) - purple = UDP mode active
    strip[0] = (50, 0, 100)  # GRB: purple
    strip.write()
    buffer[0] = 50   # G
    buffer[1] = 0    # R
    buffer[2] = 100  # B

    # Start LED writer thread
    _thread.start_new_thread(led_writer, ())

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', UDP_PORT))
    sock.settimeout(0.01)  # Fast polling

    print("[UDP] Listening on port", UDP_PORT)
    print("[UDP] Format: (idx_lo, idx_hi, G, R, B) x N")
    print("[UDP] Send 0xFF to exit")

    buf = memoryview(buffer)

    while running:
        try:
            data, addr = sock.recvfrom(4096)
            length = len(data)

            if length == 0:
                continue

            # Exit command: single byte 0xFF
            if length == 1 and data[0] == 0xFF:
                print("[UDP] Exit command received")
                running = False
                break

            # LED updates: 5 bytes per LED (idx_lo, idx_hi, G, R, B)
            if length >= 5:
                # Process as many complete 5-byte chunks as possible
                for i in range(0, (length // 5) * 5, 5):
                    idx = data[i] | (data[i+1] << 8)
                    if idx < NUM_LEDS:
                        bidx = idx * 3
                        buf[bidx] = data[i+2]      # G
                        buf[bidx+1] = data[i+3]    # R
                        buf[bidx+2] = data[i+4]    # B
                new_data = True  # Signal LED writer to update

        except OSError:
            pass  # Timeout
        except Exception as e:
            print("[UDP] Error:", e)

    # Cleanup
    sock.close()
    running = False

    # Clear LEDs
    for i in range(NUM_LEDS):
        strip[i] = (0, 0, 0)
    strip.write()

    # Remove flag and reboot
    clear_flag()
    print("[UDP] Rebooting to normal mode...")
    time.sleep(1)
    machine.reset()


if __name__ == "__main__":
    run()
