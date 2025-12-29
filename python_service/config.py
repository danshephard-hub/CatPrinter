import os
import json
import logging

logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from Home Assistant options.json or environment variables"""
    config = {}

    # Try to load from /data/options.json (Home Assistant addon config)
    try:
        config_path = '/data/options.json'
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info("Loaded configuration from /data/options.json")
        else:
            logger.warning("Configuration file not found, using environment variables")
    except Exception as e:
        logger.error(f"Error loading configuration file: {e}")

    # Override with environment variables if present
    if os.getenv('PRINTER_MAC'):
        config['printer_mac'] = os.getenv('PRINTER_MAC')
    if os.getenv('AUTO_CONNECT'):
        config['auto_connect'] = os.getenv('AUTO_CONNECT').lower() in ('true', '1', 'yes')
    if os.getenv('PRINT_INTENSITY'):
        config['print_intensity'] = int(os.getenv('PRINT_INTENSITY'))
    if os.getenv('DITHER_METHOD'):
        config['dither_method'] = os.getenv('DITHER_METHOD')
    if os.getenv('LOG_LEVEL'):
        config['log_level'] = os.getenv('LOG_LEVEL')

    # Set defaults if not specified
    config.setdefault('printer_mac', '')
    config.setdefault('auto_connect', True)
    config.setdefault('print_intensity', 128)
    config.setdefault('dither_method', 'floyd-steinberg')
    config.setdefault('log_level', 'info')

    return config


def get_log_level(config):
    """Convert log level string to logging constant"""
    level_map = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR
    }
    return level_map.get(config.get('log_level', 'info').lower(), logging.INFO)
