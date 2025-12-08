#!/usr/bin/env python3
# boot.py - minimal boot, main logic in main.py
import gc
import machine
import neopixel
import network
import time

# Status LED on pin 8 (built-in WS LED on ESP32-C3)
STATUS_LED_PIN = 8
status_led = neopixel.NeoPixel(machine.Pin(STATUS_LED_PIN), 1)

# Set status LED (RGB order)
def set_status(r, g, b):
    status_led[0] = (r, g, b)  # RGB order
    status_led.write()

# Boot started - RED
set_status(255, 0, 0)
print("Boot started...")

# Enable garbage collection
gc.enable()
gc.collect()

# Connect WiFi early for WebREPL
WIFI_SSID = 'wgnet'
WIFI_PASSWORD = 'bomba1235'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print("Connecting to WiFi...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(30):
        if wlan.isconnected():
            break
        set_status(0, 0, 255)
        time.sleep(0.2)
        set_status(0, 0, 50)
        time.sleep(0.2)

if wlan.isconnected():
    print("WiFi connected:", wlan.ifconfig()[0])
    # Start WebREPL
    try:
        import webrepl
        webrepl.start()
        print("WebREPL started on port 8266")
    except Exception as e:
        print("WebREPL error:", e)

print("Boot completed, starting main.py...")
