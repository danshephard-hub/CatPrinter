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

# Log startup
bashio::log.info "Starting MXW01 Printer Addon..."
bashio::log.info "Printer MAC: ${PRINTER_MAC}"
bashio::log.info "Auto-connect: ${AUTO_CONNECT}"
bashio::log.info "Print Intensity: ${PRINT_INTENSITY}"
bashio::log.info "Dither Method: ${DITHER_METHOD}"

# Configure D-Bus for Bluetooth
bashio::log.info "Configuring D-Bus for Bluetooth..."

# Check if host D-Bus socket is available (Home Assistant OS shares this)
if [ -e /var/run/dbus/system_bus_socket ]; then
    bashio::log.info "Using host D-Bus socket"
    export DBUS_SYSTEM_BUS_ADDRESS=unix:path=/var/run/dbus/system_bus_socket
else
    # Start our own D-Bus if not available from host
    bashio::log.info "Starting local D-Bus daemon..."
    mkdir -p /var/run/dbus
    rm -f /var/run/dbus/pid
    dbus-daemon --system --fork || bashio::log.warning "D-Bus may already be running"
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
