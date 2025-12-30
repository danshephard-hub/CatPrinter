#!/usr/bin/env python3
"""
MXW01 Thermal Printer Home Assistant Addon
Main orchestrator service
"""

import logging
import signal
import sys
import time
from config import load_config, get_log_level
from printer_client import PrinterClient
from web_ui import create_app

# Global references for cleanup
printer_client = None
app = None


def setup_logging(config):
    """Configure logging"""
    log_level = get_log_level(config)

    logging.basicConfig(
        level=log_level,
        format='[%(levelname)s] %(name)s: %(message)s',
        stream=sys.stdout
    )

    return logging.getLogger(__name__)


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal, cleaning up...")

    if printer_client:
        try:
            printer_client.stop()
        except Exception as e:
            logger.error(f"Error stopping printer client: {e}")

    sys.exit(0)


def main():
    global printer_client, app, logger

    # Load configuration
    config = load_config()

    # Setup logging
    logger = setup_logging(config)
    logger.info("MXW01 Thermal Printer Addon starting...")
    logger.info(f"Configuration: {config}")

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Create printer client
        logger.info("Initializing Bluetooth printer client...")
        printer_client = PrinterClient()

        # Wait for event loop to initialize
        time.sleep(1)

        # Auto-connect if configured
        if config.get('auto_connect'):
            mac = config.get('printer_mac') or None
            if mac:
                logger.info(f"Auto-connecting to printer: {mac}")
            else:
                logger.info("Auto-connecting to any available MXW01 printer...")
            try:
                result = printer_client.connect(mac)
                logger.info(f"Auto-connect successful: {result}")
            except Exception as e:
                logger.error(f"Auto-connect failed: {e}")
                logger.info("Continuing without connection - you can connect manually via web UI")

        # Set initial printer settings
        try:
            if config.get('print_intensity'):
                printer_client.set_intensity(config['print_intensity'])
            if config.get('dither_method'):
                printer_client.set_dither_method(config['dither_method'])
        except Exception as e:
            logger.warning(f"Failed to set initial printer settings: {e}")

        # Create Flask app
        logger.info("Starting web server...")
        app = create_app(printer_client, config)

        # Start Flask server
        logger.info("Web UI available on port 8099")
        logger.info("MXW01 Printer Addon is ready!")

        app.run(
            host='0.0.0.0',
            port=8099,
            debug=False,
            use_reloader=False
        )

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        if printer_client:
            printer_client.stop()
        sys.exit(1)


if __name__ == '__main__':
    main()
