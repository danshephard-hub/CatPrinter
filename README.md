# MXW01 Thermal Printer Home Assistant Addon

Control your MXW01 Bluetooth thermal printer directly from Home Assistant!

## Features

- Print text messages with customizable font sizes
- Print images from local files or URLs
- Web UI for manual printer control and testing
- Auto-connect to printer on startup
- Configurable print intensity and dithering methods
- Integration with Home Assistant automations
- Support for automation-triggered printing

## Installation

### Method 1: Local Addon

1. Copy this entire directory to your Home Assistant addons folder:
   ```
   /addons/mxw01-printer-addon/
   ```

2. Restart Home Assistant or reload addons

3. Go to **Settings > Add-ons > Local Add-ons**

4. Find "MXW01 Thermal Printer" and click on it

5. Click **INSTALL**

### Method 2: Custom Repository (Future)

Once published, you can add this as a custom repository in the Home Assistant Add-on Store.

## Configuration

Before starting the addon, configure the following options:

| Option | Description | Default |
|--------|-------------|---------|
| `printer_mac` | Bluetooth MAC address of your MXW01 printer | "" (empty) |
| `auto_connect` | Automatically connect to printer on startup | true |
| `print_intensity` | Print darkness (0-255) | 128 |
| `dither_method` | Image dithering algorithm | "floyd-steinberg" |
| `log_level` | Logging verbosity | "info" |

### Finding Your Printer's MAC Address

To find your MXW01 printer's Bluetooth MAC address:

1. Use your phone's Bluetooth settings to scan for devices
2. Look for a device named "MXW01" or similar
3. The MAC address will be shown (format: `AA:BB:CC:DD:EE:FF`)

Alternatively, on Linux/Home Assistant:
```bash
bluetoothctl
scan on
# Look for MXW01 in the list
```

## Web UI

Once the addon is running, access the web interface through Home Assistant:

**Settings > Add-ons > MXW01 Thermal Printer > OPEN WEB UI**

The web UI provides:
- Real-time printer status
- Connection controls
- Text printing with preview
- Image printing from URLs or file paths
- Test print functionality
- Settings adjustment

## Home Assistant Integration

### Setting Up REST Commands

Add the following to your `configuration.yaml`:

```yaml
rest_command:
  mxw01_print_text:
    url: "http://a0d7b954-mxw01-printer:8099/api/print/text"
    method: POST
    content_type: "application/json"
    payload: '{"text": "{{ text }}", "font_size": {{ font_size | default(24) }}}'

  mxw01_print_image:
    url: "http://a0d7b954-mxw01-printer:8099/api/print/image"
    method: POST
    content_type: "application/json"
    payload: '{"image_path": "{{ image_path }}"}'

  mxw01_connect:
    url: "http://a0d7b954-mxw01-printer:8099/api/connect"
    method: POST
    content_type: "application/json"
    payload: '{"mac_address": "{{ mac_address }}"}'

  mxw01_disconnect:
    url: "http://a0d7b954-mxw01-printer:8099/api/disconnect"
    method: POST
    content_type: "application/json"
```

**Note:** Replace `a0d7b954-mxw01-printer` with your actual addon hostname if different.

After adding, restart Home Assistant or reload configuration.

### Usage Examples

#### Print Text from Automation

```yaml
automation:
  - alias: "Print door alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door
        to: "on"
    action:
      - service: rest_command.mxw01_print_text
        data:
          text: "Front door opened at {{ now().strftime('%H:%M') }}"
          font_size: 24
```

#### Print Morning Weather Report

```yaml
automation:
  - alias: "Morning weather print"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: rest_command.mxw01_print_text
        data:
          text: |
            Weather Today
            {{ states('sensor.temperature') }}°C
            {{ states('sensor.weather_condition') }}
            Have a great day!
```

#### Print Security Camera Snapshot

```yaml
automation:
  - alias: "Print motion snapshot"
    trigger:
      - platform: state
        entity_id: binary_sensor.motion_detected
        to: "on"
    action:
      - service: camera.snapshot
        data:
          entity_id: camera.front_door
          filename: /config/www/motion_snapshot.jpg
      - delay: "00:00:02"
      - service: rest_command.mxw01_print_image
        data:
          image_path: "/config/www/motion_snapshot.jpg"
```

#### Print Package Delivery Notification

```yaml
automation:
  - alias: "Package delivered"
    trigger:
      - platform: state
        entity_id: binary_sensor.mailbox
        to: "on"
    action:
      - service: rest_command.mxw01_print_text
        data:
          text: |
            PACKAGE DELIVERED
            {{ now().strftime('%B %d, %Y') }}
            {{ now().strftime('%I:%M %p') }}
            Check your mailbox!
          font_size: 20
```

## API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Get printer status |
| `/api/connect` | POST | Connect to printer |
| `/api/disconnect` | POST | Disconnect from printer |
| `/api/print/text` | POST | Print text |
| `/api/print/image` | POST | Print image |
| `/api/print/test` | POST | Print test page |
| `/api/settings` | POST | Update printer settings |

### API Examples

#### Print Text
```bash
curl -X POST http://homeassistant.local:8099/api/print/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World!", "font_size": 24}'
```

#### Print Image
```bash
curl -X POST http://homeassistant.local:8099/api/print/image \
  -H "Content-Type: application/json" \
  -d '{"image_path": "https://example.com/image.jpg"}'
```

## Troubleshooting

### Addon won't start

1. Check the addon logs: **Settings > Add-ons > MXW01 Thermal Printer > Log**
2. Ensure your Home Assistant host has Bluetooth capability
3. Verify the Bluetooth adapter is working: `bluetoothctl` in terminal

### Printer won't connect

1. Verify the MAC address is correct
2. Ensure the printer is powered on and in range
3. Try manually pairing via Home Assistant terminal:
   ```bash
   bluetoothctl
   scan on
   pair AA:BB:CC:DD:EE:FF
   trust AA:BB:CC:DD:EE:FF
   ```
4. Check if another device is connected to the printer
5. Restart the printer

### Prints are too dark/light

Adjust the `print_intensity` setting (0-255):
- Lower values = lighter prints
- Higher values = darker prints
- Default is 128

### Images print poorly

Try different dithering methods:
- `floyd-steinberg` - Best for photos (default)
- `atkinson` - Good for line art
- `bayer` - Fast, ordered dithering
- `none` - No dithering (pure black/white)

### Permission errors

Ensure the addon has the required permissions in `config.yaml`:
- `bluetooth: true`
- `dbus: system`

## Technical Details

### Architecture

```
Home Assistant
  └─> Python Service (Flask + HA Integration)
      └─> Node.js Bridge (JSON-RPC)
          └─> mxw01-thermal-printer library
              └─> Bluetooth → MXW01 Printer
```

### Dependencies

- **Node.js Libraries:** `@clementvp/mxw01-thermal-printer`, `canvas`, `@stoprocent/noble`
- **Python Libraries:** `flask`, `pillow`, `pyyaml`, `requests`
- **System:** `bluez`, `dbus`

## Contributing

Issues and pull requests are welcome! Please report bugs or suggest features through GitHub issues.

## License

This addon uses the [mxw01-thermal-printer](https://github.com/clementvp/mxw01-thermal-printer) library.

## Credits

- MXW01 Printer Library: [@clementvp](https://github.com/clementvp)
- Home Assistant: [home-assistant.io](https://www.home-assistant.io/)

## Support

For issues and questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review addon logs
- Open an issue on GitHub
