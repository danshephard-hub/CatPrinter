import asyncio
import json
import logging
import subprocess
import threading
import queue

logger = logging.getLogger(__name__)


class PrinterBridge:
    """Bridge to Node.js printer service using JSON-RPC over stdio"""

    def __init__(self):
        self.process = None
        self.request_id = 0
        self.pending_requests = {}
        self.response_queue = queue.Queue()
        self.reader_thread = None
        self.lock = threading.Lock()

    def start(self):
        """Start Node.js bridge process"""
        try:
            logger.info("Starting Node.js bridge process...")
            self.process = subprocess.Popen(
                ['node', '/app/node_service/index.js'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )

            # Start thread to read responses
            self.reader_thread = threading.Thread(target=self._read_responses, daemon=True)
            self.reader_thread.start()

            # Start thread to read stderr for logging
            stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
            stderr_thread.start()

            logger.info("Node.js bridge process started")
        except Exception as e:
            logger.error(f"Failed to start Node.js bridge: {e}")
            raise

    def _read_responses(self):
        """Read JSON-RPC responses from Node.js stdout"""
        while self.process and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break

                line = line.decode('utf-8').strip()
                if not line:
                    continue

                logger.debug(f"Received from Node.js: {line}")
                response = json.loads(line)

                request_id = response.get('id')
                if request_id in self.pending_requests:
                    future = self.pending_requests.pop(request_id)

                    if 'error' in response:
                        future['error'] = response['error']['message']
                    else:
                        future['result'] = response.get('result')

                    future['done'] = True

            except Exception as e:
                logger.error(f"Error reading response: {e}")

    def _read_stderr(self):
        """Read and log stderr from Node.js process"""
        while self.process and self.process.poll() is None:
            try:
                line = self.process.stderr.readline()
                if not line:
                    break

                line = line.decode('utf-8').strip()
                if line:
                    logger.info(f"Node.js: {line}")
            except Exception as e:
                logger.error(f"Error reading stderr: {e}")

    def _send_request(self, method, params=None, timeout=30):
        """Send JSON-RPC request to Node.js and wait for response"""
        if not self.process or self.process.poll() is not None:
            raise Exception("Node.js bridge process is not running")

        with self.lock:
            self.request_id += 1
            request_id = self.request_id

            request = {
                'jsonrpc': '2.0',
                'id': request_id,
                'method': method,
                'params': params or {}
            }

            # Create future for response
            future = {'done': False, 'result': None, 'error': None}
            self.pending_requests[request_id] = future

            # Send request
            request_json = json.dumps(request) + '\n'
            logger.debug(f"Sending to Node.js: {request_json.strip()}")

            try:
                self.process.stdin.write(request_json.encode('utf-8'))
                self.process.stdin.flush()
            except Exception as e:
                self.pending_requests.pop(request_id, None)
                raise Exception(f"Failed to send request: {e}")

        # Wait for response
        start_time = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
        while not future['done']:
            if timeout and asyncio.get_event_loop().is_running():
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    self.pending_requests.pop(request_id, None)
                    raise Exception(f"Request timeout after {timeout}s")

            import time
            time.sleep(0.1)

        if future['error']:
            raise Exception(future['error'])

        return future['result']

    # Public API methods

    def connect(self, mac_address):
        """Connect to printer via Bluetooth"""
        logger.info(f"Connecting to printer: {mac_address}")
        return self._send_request('connect', {'mac': mac_address})

    def disconnect(self):
        """Disconnect from printer"""
        logger.info("Disconnecting from printer")
        return self._send_request('disconnect')

    def print_text(self, text, font_size=24):
        """Print text"""
        logger.info(f"Printing text: {text[:50]}...")
        return self._send_request('print_text', {
            'text': text,
            'fontSize': font_size
        })

    def print_image(self, image_path):
        """Print image from file path"""
        logger.info(f"Printing image: {image_path}")
        return self._send_request('print_image', {
            'path': image_path
        })

    def get_status(self):
        """Get printer status"""
        return self._send_request('get_status')

    def set_intensity(self, intensity):
        """Set print intensity (0-255)"""
        logger.info(f"Setting print intensity: {intensity}")
        return self._send_request('set_intensity', {
            'intensity': intensity
        })

    def set_dither_method(self, method):
        """Set dithering method"""
        logger.info(f"Setting dither method: {method}")
        return self._send_request('set_dither_method', {
            'method': method
        })

    def stop(self):
        """Stop Node.js bridge process"""
        if self.process:
            logger.info("Stopping Node.js bridge process")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
