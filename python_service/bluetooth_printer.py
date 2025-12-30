"""
MXW01 Thermal Printer - Bluetooth Client using Bleak

Uses Home Assistant's Bluetooth integration to connect to MXW01 thermal printers.
Compatible with ESPHome Bluetooth proxies.
"""

import asyncio
import logging
from typing import Optional
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from PIL import Image
import io

logger = logging.getLogger(__name__)

# MXW01 Printer GATT UUIDs (same as cat printer protocol)
SERVICE_UUID = "0000ae30-0000-1000-8000-00805f9b34fb"
CHAR_TX_UUID = "0000ae01-0000-1000-8000-00805f9b34fb"  # Write to printer
CHAR_RX_UUID = "0000ae02-0000-1000-8000-00805f9b34fb"  # Notifications from printer

PRINTER_WIDTH = 384  # pixels


class MXW01Printer:
    """MXW01 Thermal Printer Client using Bleak"""

    def __init__(self):
        self.client: Optional[BleakClient] = None
        self.device: Optional[BLEDevice] = None
        self.print_intensity = 128  # 0-255
        self.dither_method = "floyd-steinberg"

    async def scan_for_printers(self, timeout: float = 10.0):
        """Scan for MXW01 printers"""
        logger.info(f"Scanning for MXW01 printers (timeout: {timeout}s)...")

        def detection_callback(device: BLEDevice, advertisement_data):
            # Check if device advertises our service UUID
            if SERVICE_UUID.lower() in [
                str(uuid).lower() for uuid in advertisement_data.service_uuids
            ]:
                logger.info(f"Found MXW01 printer: {device.name} ({device.address})")

        scanner = BleakScanner(detection_callback=detection_callback)

        devices = await scanner.discover(timeout=timeout, return_adv=False)

        # Filter for devices with our service
        printers = []
        for device in devices:
            try:
                async with BleakClient(device) as client:
                    services = await client.get_services()
                    if any(str(s.uuid).lower() == SERVICE_UUID.lower() for s in services):
                        printers.append(device)
                        logger.info(f"Verified printer: {device.name} ({device.address})")
            except Exception as e:
                logger.debug(f"Could not verify device {device.address}: {e}")
                continue

        return printers

    async def connect(self, mac_address: Optional[str] = None):
        """Connect to MXW01 printer by MAC address or scan for first available"""
        try:
            if mac_address:
                logger.info(f"Connecting to printer at {mac_address}...")
                # Scan with filter for specific MAC
                devices = await BleakScanner.discover(timeout=30.0)
                self.device = next(
                    (d for d in devices if d.address.lower() == mac_address.lower()),
                    None
                )
                if not self.device:
                    raise Exception(f"Printer with MAC {mac_address} not found")
            else:
                logger.info("Scanning for any MXW01 printer...")
                printers = await self.scan_for_printers(timeout=30.0)
                if not printers:
                    raise Exception("No MXW01 printers found")
                self.device = printers[0]

            # Connect to device
            self.client = BleakClient(self.device)
            await self.client.connect()

            logger.info(
                f"Connected to {self.device.name} ({self.device.address})"
            )

            return {
                "success": True,
                "connected": True,
                "deviceName": self.device.name,
                "deviceAddress": self.device.address,
            }

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise Exception(f"Connection failed: {str(e)}")

    async def disconnect(self):
        """Disconnect from printer"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            logger.info("Disconnected from printer")
        return {"success": True}

    async def _send_command(self, data: bytes):
        """Send raw command to printer"""
        if not self.client or not self.client.is_connected:
            raise Exception("Printer not connected")

        # Split data into chunks (max 20 bytes per BLE packet)
        chunk_size = 20
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            await self.client.write_gatt_char(CHAR_TX_UUID, chunk, response=False)
            await asyncio.sleep(0.01)  # Small delay between chunks

    def _encode_image_data(self, image: Image.Image) -> bytes:
        """Encode image for MXW01 printer"""
        # Convert to grayscale
        img = image.convert('L')

        # Resize to printer width while maintaining aspect ratio
        aspect_ratio = img.height / img.width
        new_height = int(PRINTER_WIDTH * aspect_ratio)
        img = img.resize((PRINTER_WIDTH, new_height), Image.Resampling.LANCZOS)

        # Apply dithering
        if self.dither_method == "floyd-steinberg":
            img = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
        elif self.dither_method == "none":
            img = img.convert('1', dither=Image.Dither.NONE)
        else:
            img = img.convert('1')

        # Convert to 1-bit bitmap
        width, height = img.size
        pixels = list(img.getdata())

        # Pack pixels into bytes (8 pixels per byte)
        data = bytearray()
        for y in range(height):
            row = bytearray()
            for x in range(0, width, 8):
                byte = 0
                for bit in range(8):
                    if x + bit < width:
                        pixel_index = y * width + x + bit
                        if pixels[pixel_index] > 127:  # White
                            byte |= (1 << (7 - bit))
                row.append(byte)
            data.extend(row)

        return bytes(data)

    async def print_image(self, image_path: str):
        """Print image from file"""
        logger.info(f"Printing image: {image_path}")

        # Load image
        img = Image.open(image_path)

        # Encode for printer
        image_data = self._encode_image_data(img)

        # Send print commands
        await self._send_command(b'\x10\xff\xfe\x01')  # Initialize
        await asyncio.sleep(0.1)

        # Send image data
        await self._send_command(image_data)

        # Feed paper
        await self._send_command(b'\x1a\xff\xff')

        logger.info("Image sent to printer")
        return {"success": True}

    async def print_text(self, text: str, font_size: int = 24):
        """Print text by rendering to image first"""
        logger.info(f"Printing text (size {font_size}): {text[:50]}...")

        from PIL import ImageDraw, ImageFont

        # Estimate height needed
        lines = text.split('\n')
        line_height = font_size + 10
        height = len(lines) * line_height + 40

        # Create image
        img = Image.new('RGB', (PRINTER_WIDTH, height), 'white')
        draw = ImageDraw.Draw(img)

        # Try to use default font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Draw text
        y = 20
        for line in lines:
            draw.text((10, y), line, fill='black', font=font)
            y += line_height

        # Crop to actual content
        bbox = img.getbbox()
        if bbox:
            img = img.crop((0, 0, PRINTER_WIDTH, bbox[3] + 20))

        # Print the image
        return await self.print_image_direct(img)

    async def print_image_direct(self, image: Image.Image):
        """Print PIL Image directly"""
        logger.info("Printing image directly...")

        # Encode for printer
        image_data = self._encode_image_data(image)

        # Send print commands
        await self._send_command(b'\x10\xff\xfe\x01')  # Initialize
        await asyncio.sleep(0.1)

        # Send image data
        await self._send_command(image_data)

        # Feed paper
        await self._send_command(b'\x1a\xff\xff')

        logger.info("Image sent to printer")
        return {"success": True}

    def set_intensity(self, intensity: int):
        """Set print intensity (0-255)"""
        self.print_intensity = max(0, min(255, intensity))
        logger.info(f"Print intensity set to {self.print_intensity}")
        return {"success": True}

    def set_dither_method(self, method: str):
        """Set dithering method"""
        self.dither_method = method
        logger.info(f"Dither method set to {self.dither_method}")
        return {"success": True}

    def is_connected(self):
        """Check if printer is connected"""
        return self.client is not None and self.client.is_connected

    def get_status(self):
        """Get printer status"""
        return {
            "connected": self.is_connected(),
            "printing": False,  # TODO: Track printing state
            "deviceName": self.device.name if self.device else None,
            "deviceAddress": self.device.address if self.device else None,
        }
