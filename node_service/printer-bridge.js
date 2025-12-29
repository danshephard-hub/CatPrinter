const { ThermalPrinterClient, NodeBluetoothAdapter } = require('mxw01-thermal-printer');
const { createCanvas, loadImage } = require('canvas');
const fs = require('fs').promises;

class PrinterBridge {
    constructor() {
        this.printer = null;
        this.adapter = null;
    }

    async connect(macAddress) {
        try {
            // Create adapter (no parameters)
            this.adapter = new NodeBluetoothAdapter();

            // Request device (scans for MXW01 printers)
            const device = await this.adapter.requestDevice();

            // Note: requestDevice() auto-discovers MXW01 printers
            // If MAC filtering is needed, it would happen here
            // For now, we'll connect to the first discovered device

            // Create printer client and connect
            const connection = await this.adapter.connect(device);
            this.printer = new ThermalPrinterClient(this.adapter);

            return {
                success: true,
                connected: true,
                deviceName: device.name,
                deviceId: device.id
            };
        } catch (error) {
            throw new Error(`Connection failed: ${error.message}`);
        }
    }

    async disconnect() {
        if (this.printer) {
            await this.printer.disconnect();
        }
        return { success: true };
    }

    async printText(text, fontSize = 24) {
        if (!this.printer || !this.printer.isConnected) {
            throw new Error('Printer not connected');
        }

        // Create canvas with text
        const canvas = createCanvas(384, 600);
        const ctx = canvas.getContext('2d');

        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = 'black';
        ctx.font = `${fontSize}px sans-serif`;

        // Word wrap
        const words = text.split(' ');
        let line = '';
        let y = fontSize + 10;
        const maxWidth = canvas.width - 20;

        for (const word of words) {
            const testLine = line + word + ' ';
            const metrics = ctx.measureText(testLine);

            if (metrics.width > maxWidth && line !== '') {
                ctx.fillText(line.trim(), 10, y);
                line = word + ' ';
                y += fontSize + 5;
            } else {
                line = testLine;
            }
        }
        if (line.trim()) {
            ctx.fillText(line.trim(), 10, y);
        }

        // Crop canvas to actual content height
        const actualHeight = Math.min(y + 20, canvas.height);
        const croppedCanvas = createCanvas(384, actualHeight);
        const croppedCtx = croppedCanvas.getContext('2d');
        croppedCtx.drawImage(canvas, 0, 0);

        // Print canvas
        const imageData = croppedCtx.getImageData(0, 0, croppedCanvas.width, croppedCanvas.height);
        await this.printer.print(imageData);

        return { success: true };
    }

    async printImage(imagePath) {
        if (!this.printer || !this.printer.isConnected) {
            throw new Error('Printer not connected');
        }

        // Load and resize image
        const image = await loadImage(imagePath);
        const targetWidth = 384;
        const targetHeight = Math.floor(targetWidth * image.height / image.width);

        const canvas = createCanvas(targetWidth, targetHeight);
        const ctx = canvas.getContext('2d');

        ctx.drawImage(image, 0, 0, targetWidth, targetHeight);

        // Print
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        await this.printer.print(imageData);

        return { success: true };
    }

    async getStatus() {
        if (!this.printer) {
            return {
                connected: false,
                printing: false
            };
        }

        return {
            connected: this.printer.isConnected,
            printing: this.printer.isPrinting || false,
            state: this.printer.printerState || 'unknown'
        };
    }

    async setIntensity(intensity) {
        if (this.printer) {
            this.printer.setPrintIntensity(intensity);
        }
        return { success: true };
    }

    async setDitherMethod(method) {
        if (this.printer) {
            this.printer.setDitherMethod(method);
        }
        return { success: true };
    }
}

module.exports = PrinterBridge;
