#!/usr/bin/with-contenv bashio

# Read configuration
CONFIG_PATH=/data/options.json

# Export configuration as environment variables
export PRINTER_MAC=$(bashio::config 'printer_mac')
export AUTO_CONNECT=$(bashio::config 'auto_connect')
export PRINT_INTENSITY=$(bashio::config 'print_intensity')
export DITHER_METHOD=$(bashio::config 'dither_method')
export LOG_LEVEL=$(bashio::config 'log_level')

# Log startup
bashio::log.info "Starting MXW01 Printer Addon..."
bashio::log.info "Printer MAC: ${PRINTER_MAC:-Any available printer}"
bashio::log.info "Auto-connect: ${AUTO_CONNECT}"
bashio::log.info "Print Intensity: ${PRINT_INTENSITY}"
bashio::log.info "Dither Method: ${DITHER_METHOD}"
bashio::log.info "Using Home Assistant Bluetooth Integration"

# Start Python service
cd /app
exec python3 -u python_service/main.py
