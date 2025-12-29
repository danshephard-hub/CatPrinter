from flask import Flask, render_template, request, jsonify
import logging
import os
from datetime import datetime
import tempfile
import requests

logger = logging.getLogger(__name__)


def create_app(bridge, config):
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config['BRIDGE'] = bridge
    app.config['CONFIG'] = config

    @app.route('/')
    def index():
        """Main web UI page"""
        return render_template('index.html', config=config)

    @app.route('/api/status')
    def status():
        """Get printer status"""
        try:
            bridge = app.config['BRIDGE']
            status_data = bridge.get_status()
            return jsonify(status_data)
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/connect', methods=['POST'])
    def connect():
        """Connect to printer"""
        try:
            data = request.get_json() or {}
            mac = data.get('mac_address') or app.config['CONFIG'].get('printer_mac')

            if not mac:
                return jsonify({'error': 'MAC address required'}), 400

            bridge = app.config['BRIDGE']
            result = bridge.connect(mac)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error connecting: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/disconnect', methods=['POST'])
    def disconnect():
        """Disconnect from printer"""
        try:
            bridge = app.config['BRIDGE']
            result = bridge.disconnect()
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/print/text', methods=['POST'])
    def print_text():
        """Print text"""
        try:
            data = request.get_json() or {}
            text = data.get('text', '')
            font_size = data.get('font_size', 24)

            if not text:
                return jsonify({'error': 'Text required'}), 400

            bridge = app.config['BRIDGE']
            result = bridge.print_text(text, font_size)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error printing text: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/print/image', methods=['POST'])
    def print_image():
        """Print image from URL or file path"""
        try:
            data = request.get_json() or {}
            image_path = data.get('image_path', '')

            if not image_path:
                return jsonify({'error': 'Image path required'}), 400

            # If URL, download it first
            if image_path.startswith('http://') or image_path.startswith('https://'):
                temp_path = download_image(image_path)
                image_path = temp_path

            bridge = app.config['BRIDGE']
            result = bridge.print_image(image_path)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error printing image: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/print/test', methods=['POST'])
    def print_test():
        """Print test page"""
        try:
            test_text = (
                "MXW01 Printer Test\n"
                "Home Assistant Addon\n"
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                "====================\n"
                "If you can read this,\n"
                "the printer is working!"
            )

            bridge = app.config['BRIDGE']
            result = bridge.print_text(test_text, 20)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error printing test: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/settings', methods=['POST'])
    def update_settings():
        """Update printer settings"""
        try:
            data = request.get_json() or {}
            bridge = app.config['BRIDGE']

            intensity = data.get('intensity')
            dither = data.get('dither_method')

            if intensity is not None:
                bridge.set_intensity(int(intensity))

            if dither:
                bridge.set_dither_method(dither)

            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return jsonify({'error': str(e)}), 500

    return app


def download_image(url):
    """Download image from URL to temporary file"""
    logger.info(f"Downloading image from {url}")

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Create temporary file
    suffix = os.path.splitext(url)[1] or '.jpg'
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

    temp_file.write(response.content)
    temp_file.close()

    logger.info(f"Downloaded image to {temp_file.name}")
    return temp_file.name
