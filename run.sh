#!/usr/bin/with-contenv bashio

# Read configuration
CONFIG_PATH=/data/options.json

# Export configuration as environment variables
export PRINTER_MAC=$(bashio::config 'printer_mac')
export AUTO_CONNECT=$(bashio::config 'auto_connect')
export PRINT_INTENSITY=$(bashio::config 'print_intensity')
export DITHER_METHOD=$(bashio::config 'dither_method')
export LOG_LEVEL=$(bashio::config 'log_level')

# Noble environment variables
export NOBLE_MULTI_ROLE=1
export NOBLE_REPORT_ALL_HCI_EVENTS=1
export DEBUG=noble*

# Debug: Show environment
bashio::log.info "Environment check..."
bashio::log.info "USER: $(whoami)"
bashio::log.info "Groups: $(groups)"
bashio::log.info "Bluetooth devices:"
ls -la /dev/bluetooth* 2>/dev/null || bashio::log.info "  No /dev/bluetooth*"
ls -la /dev/tty* 2>/dev/null | grep -i blue || bashio::log.info "  No /dev/tty Bluetooth"
ls -la /sys/class/bluetooth/ 2>/dev/null || bashio::log.info "  No /sys/class/bluetooth"

# Log startup
bashio::log.info "Starting MXW01 Printer Addon..."
bashio::log.info "Printer MAC: ${PRINTER_MAC}"
bashio::log.info "Auto-connect: ${AUTO_CONNECT}"
bashio::log.info "Print Intensity: ${PRINT_INTENSITY}"
bashio::log.info "Dither Method: ${DITHER_METHOD}"

# Configure D-Bus for Bluetooth
bashio::log.info "Configuring D-Bus for Bluetooth..."

# Debug: Check what's available
bashio::log.info "Checking for D-Bus sockets..."
ls -la /var/run/dbus/ 2>/dev/null || bashio::log.info "No /var/run/dbus directory"
ls -la /run/dbus/ 2>/dev/null || bashio::log.info "No /run/dbus directory"
ls -la /host/run/dbus/ 2>/dev/null || bashio::log.info "No /host/run/dbus directory"

# Check multiple possible D-Bus socket locations
DBUS_SOCKET=""
if [ -S /var/run/dbus/system_bus_socket ]; then
    DBUS_SOCKET="/var/run/dbus/system_bus_socket"
elif [ -S /run/dbus/system_bus_socket ]; then
    DBUS_SOCKET="/run/dbus/system_bus_socket"
elif [ -S /host/run/dbus/system_bus_socket ]; then
    DBUS_SOCKET="/host/run/dbus/system_bus_socket"
fi

if [ -n "$DBUS_SOCKET" ]; then
    bashio::log.info "Found host D-Bus socket at: $DBUS_SOCKET"
    export DBUS_SYSTEM_BUS_ADDRESS=unix:path=$DBUS_SOCKET
else
    # Start our own D-Bus if not available from host
    bashio::log.warning "No host D-Bus socket found, starting local daemon..."
    mkdir -p /var/run/dbus
    rm -f /var/run/dbus/pid
    dbus-daemon --system --fork || bashio::log.warning "D-Bus may already be running"
    export DBUS_SYSTEM_BUS_ADDRESS=unix:path=/var/run/dbus/system_bus_socket
fi

# Verify D-Bus is accessible
if command -v dbus-send >/dev/null 2>&1; then
    bashio::log.info "Testing D-Bus connection..."
    dbus-send --system --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames 2>&1 | head -5 || bashio::log.warning "D-Bus test failed"
fi

# Only start bluetoothd if it's available and not already running
if command -v bluetoothd >/dev/null 2>&1; then
    if ! pgrep -x bluetoothd >/dev/null; then
        bashio::log.info "Starting bluetoothd..."
        bluetoothd --experimental &
        sleep 2
    else
        bashio::log.info "bluetoothd already running"
    fi
else
    bashio::log.info "bluetoothd not available - using host Bluetooth stack"
fi

# Try to bring up Bluetooth adapter (may be managed by host)
if command -v hciconfig >/dev/null 2>&1; then
    bashio::log.info "Bringing up Bluetooth adapter..."
    hciconfig hci0 up 2>/dev/null || bashio::log.warning "Could not bring up hci0 (may be managed by host)"
fi

# Start Python service
bashio::log.info "Starting Python service..."
cd /app
exec python3 -u python_service/main.py
