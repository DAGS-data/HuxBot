---
name: hardware_control
description: Control Arduino/ESP32 hardware — GPIO, servos, sensors, cameras
trigger: /hardware
---

# Hardware Control Skill

You have access to hardware tools for controlling an Arduino or ESP32 board connected via USB serial or WiFi.

## Available Tools

| Tool | Purpose |
|------|---------|
| `hardware_pin_mode` | Set a pin as INPUT, OUTPUT, or INPUT_PULLUP |
| `hardware_digital_read` | Read HIGH (1) or LOW (0) from a digital pin |
| `hardware_digital_write` | Write HIGH (1) or LOW (0) to a digital pin |
| `hardware_analog_read` | Read analog value 0–1023 from an analog pin |
| `hardware_servo_write` | Move a servo to 0–180 degrees |
| `hardware_read_sensor` | Read a named sensor (e.g. "dht11_temp", "ultrasonic_1") |
| `hardware_capture_image` | Capture a photo from the board camera |

## Pin Numbering

- Use Arduino-style pin numbers: digital pins 0–13, analog pins 0–5 (as integers).
- For ESP32: use GPIO numbers directly (e.g. 2, 4, 12, 13, 15, 25, 26, 27, 32, 33).
- Analog pins on ESP32 support values 0–4095.

## Safety Notes

- **Always set pin mode** before reading or writing a pin.
- **Never write to a pin configured as INPUT** — this can damage hardware.
- **Servo angles** must be between 0 and 180 degrees.
- **Ask the user before actuating motors or servos** if the physical setup is unknown.
- If a command returns an error, report it clearly and do not retry automatically.

## Example Workflow

1. User: "Turn on the LED on pin 13"
2. Call `hardware_pin_mode(pin=13, mode="OUTPUT")`
3. Call `hardware_digital_write(pin=13, value=1)`
4. Report: "LED on pin 13 is now ON."
