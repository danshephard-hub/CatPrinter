const readline = require('readline');
const PrinterBridge = require('./printer-bridge');

class RPCServer {
    constructor() {
        this.bridge = new PrinterBridge();
        this.rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
            terminal: false
        });

        this.setupHandlers();
        this.logMessage('Node.js bridge service started');
    }

    setupHandlers() {
        this.rl.on('line', async (line) => {
            try {
                const request = JSON.parse(line);
                this.logMessage(`Received request: ${request.method}`);

                const result = await this.handleRequest(request);

                this.sendResponse({
                    jsonrpc: '2.0',
                    id: request.id,
                    result: result
                });
            } catch (error) {
                this.logMessage(`Error: ${error.message}`);

                if (request && request.id) {
                    this.sendError(request.id, error.message);
                }
            }
        });

        this.rl.on('close', () => {
            this.logMessage('Stdin closed, shutting down');
            process.exit(0);
        });
    }

    async handleRequest(request) {
        const { method, params } = request;

        switch (method) {
            case 'connect':
                return await this.bridge.connect(params.mac);
            case 'disconnect':
                return await this.bridge.disconnect();
            case 'print_text':
                return await this.bridge.printText(params.text, params.fontSize);
            case 'print_image':
                return await this.bridge.printImage(params.path);
            case 'get_status':
                return await this.bridge.getStatus();
            case 'set_intensity':
                return await this.bridge.setIntensity(params.intensity);
            case 'set_dither_method':
                return await this.bridge.setDitherMethod(params.method);
            default:
                throw new Error(`Unknown method: ${method}`);
        }
    }

    sendResponse(response) {
        console.log(JSON.stringify(response));
    }

    sendError(id, message) {
        console.log(JSON.stringify({
            jsonrpc: '2.0',
            id: id,
            error: { message: message }
        }));
    }

    logMessage(message) {
        // Log to stderr to avoid interfering with JSON-RPC on stdout
        console.error(`[Node Bridge] ${message}`);
    }
}

// Handle uncaught errors
process.on('uncaughtException', (error) => {
    console.error(`[Node Bridge] Uncaught exception: ${error.message}`);
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error(`[Node Bridge] Unhandled rejection: ${reason}`);
});

new RPCServer();
