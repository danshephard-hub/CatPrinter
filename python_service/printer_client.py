"""
Synchronous wrapper for async Bluetooth printer client
Makes the async printer work with Flask's synchronous request handlers
"""

import asyncio
import logging
import threading
from typing import Optional
from bluetooth_printer import MXW01Printer

logger = logging.getLogger(__name__)


class PrinterClient:
    """Synchronous wrapper for MXW01Printer"""

    def __init__(self):
        self.printer = MXW01Printer()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self._start_event_loop()

    def _start_event_loop(self):
        """Start asyncio event loop in background thread"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()

        # Wait for loop to start
        import time
        timeout = 5.0
        start = time.time()
        while self.loop is None and time.time() - start < timeout:
            time.sleep(0.1)

        if self.loop is None:
            raise RuntimeError("Failed to start event loop")

        logger.info("Event loop started")

    def _run_async(self, coro, timeout=60.0):
        """Run coroutine in the background event loop"""
        if self.loop is None:
            raise RuntimeError("Event loop not running")

        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout=timeout)
        except asyncio.TimeoutError:
            raise Exception(f"Operation timed out after {timeout}s")

    def connect(self, mac_address: Optional[str] = None):
        """Connect to printer"""
        return self._run_async(self.printer.connect(mac_address), timeout=60.0)

    def disconnect(self):
        """Disconnect from printer"""
        return self._run_async(self.printer.disconnect())

    def print_text(self, text: str, font_size: int = 24):
        """Print text"""
        return self._run_async(self.printer.print_text(text, font_size))

    def print_image(self, image_path: str):
        """Print image"""
        return self._run_async(self.printer.print_image(image_path))

    def set_intensity(self, intensity: int):
        """Set print intensity"""
        return self.printer.set_intensity(intensity)

    def set_dither_method(self, method: str):
        """Set dither method"""
        return self.printer.set_dither_method(method)

    def get_status(self):
        """Get printer status"""
        return self.printer.get_status()

    def is_connected(self):
        """Check if connected"""
        return self.printer.is_connected()

    def stop(self):
        """Stop the client and event loop"""
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
            if self.thread:
                self.thread.join(timeout=5.0)
        logger.info("Printer client stopped")
