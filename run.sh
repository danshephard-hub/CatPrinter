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

# With host_dbus: true, Home Assistant OS mounts D-Bus at /run/dbus
if [ -S /run/dbus/system_bus_socket ]; then
    bashio::log.info "Using host D-Bus at /run/dbus/system_bus_socket"
    export DBUS_SYSTEM_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket

    # Test D-Bus connection
    bashio::log.info "Testing D-Bus connection..."
    if dbus-send --system --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames > /dev/null 2>&1; then
        bashio::log.info "D-Bus connection successful"

        # Check if org.bluez service is available
        bashio::log.info "Checking for BlueZ service..."
        if dbus-send --system --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames 2>&1 | grep -q "org.bluez"; then
            bashio::log.info "BlueZ service found on D-Bus"

            # List available Bluetooth adapters via D-Bus
            bashio::log.info "Checking for Bluetooth adapters..."
            dbus-send --system --print-reply --dest=org.bluez / org.freedesktop.DBus.ObjectManager.GetManagedObjects 2>&1 | grep -i adapter || bashio::log.info "No Bluetooth adapters found via D-Bus"
        else
            bashio::log.warning "BlueZ service (org.bluez) not found on D-Bus"
            bashio::log.warning "Bluetooth may not be enabled on the host system"
            bashio::log.warning "Check Home Assistant Settings -> System -> Hardware"
        fi
    else
        bashio::log.warning "D-Bus connection test failed"
    fi
else
    bashio::log.error "D-Bus socket not found at /run/dbus/system_bus_socket"
    bashio::log.error "Make sure host_dbus: true is set in config.yaml"
    exit 1
fi

# Start Python service
bashio::log.info "Starting Python service..."
cd /app
exec python3 -u python_service/main.py
