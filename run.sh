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

# Start D-Bus (required for Bluetooth/Noble)
bashio::log.info "Starting D-Bus..."
mkdir -p /var/run/dbus
dbus-daemon --system --fork || bashio::log.warning "D-Bus may already be running"

# Start bluetoothd (BlueZ daemon)
bashio::log.info "Starting bluetoothd..."
bluetoothd --experimental &
sleep 2

# Bring up Bluetooth adapter
bashio::log.info "Bringing up Bluetooth adapter..."
hciconfig hci0 up 2>/dev/null || bashio::log.warning "Could not bring up hci0"

# Start Python service
bashio::log.info "Starting Python service..."
cd /app
exec python3 -u python_service/main.py
