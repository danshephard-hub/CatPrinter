// MXW01 Printer Web UI JavaScript

// Auto-refresh status on page load
document.addEventListener('DOMContentLoaded', function() {
    refreshStatus();
    // Auto-refresh every 5 seconds
    setInterval(refreshStatus, 5000);
});

async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(endpoint, options);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Request failed');
        }

        return result;
    } catch (error) {
        throw error;
    }
}

function showMessage(message, type = 'info') {
    const messageArea = document.getElementById('message-area');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;

    messageArea.appendChild(messageDiv);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

async function refreshStatus() {
    try {
        const status = await apiCall('/api/status');

        document.getElementById('connection-status').textContent = status.connected ? 'Connected' : 'Disconnected';
        document.getElementById('connection-status').style.color = status.connected ? '#28a745' : '#dc3545';

        document.getElementById('printing-status').textContent = status.printing ? 'Yes' : 'No';
        document.getElementById('state-status').textContent = status.state || 'Unknown';

    } catch (error) {
        console.error('Error refreshing status:', error);
        document.getElementById('connection-status').textContent = 'Error';
        document.getElementById('connection-status').style.color = '#dc3545';
    }
}

async function connect() {
    const macAddress = document.getElementById('mac-address').value.trim();

    if (!macAddress) {
        showMessage('Please enter a MAC address', 'error');
        return;
    }

    try {
        showMessage('Connecting to printer...', 'info');
        const result = await apiCall('/api/connect', 'POST', { mac_address: macAddress });

        if (result.success) {
            showMessage('Successfully connected to printer!', 'success');
            refreshStatus();
        } else {
            showMessage('Connection failed', 'error');
        }
    } catch (error) {
        showMessage(`Connection error: ${error.message}`, 'error');
    }
}

async function disconnect() {
    try {
        showMessage('Disconnecting from printer...', 'info');
        const result = await apiCall('/api/disconnect', 'POST');

        if (result.success) {
            showMessage('Disconnected from printer', 'success');
            refreshStatus();
        }
    } catch (error) {
        showMessage(`Disconnect error: ${error.message}`, 'error');
    }
}

async function printText() {
    const text = document.getElementById('print-text').value.trim();
    const fontSize = parseInt(document.getElementById('font-size').value);

    if (!text) {
        showMessage('Please enter text to print', 'error');
        return;
    }

    try {
        showMessage('Printing text...', 'info');
        const result = await apiCall('/api/print/text', 'POST', {
            text: text,
            font_size: fontSize
        });

        if (result.success) {
            showMessage('Text printed successfully!', 'success');
            refreshStatus();
        }
    } catch (error) {
        showMessage(`Print error: ${error.message}`, 'error');
    }
}

async function printImage() {
    const imagePath = document.getElementById('image-path').value.trim();

    if (!imagePath) {
        showMessage('Please enter an image path or URL', 'error');
        return;
    }

    try {
        showMessage('Printing image...', 'info');
        const result = await apiCall('/api/print/image', 'POST', {
            image_path: imagePath
        });

        if (result.success) {
            showMessage('Image printed successfully!', 'success');
            refreshStatus();
        }
    } catch (error) {
        showMessage(`Print error: ${error.message}`, 'error');
    }
}

async function printTest() {
    try {
        showMessage('Printing test page...', 'info');
        const result = await apiCall('/api/print/test', 'POST');

        if (result.success) {
            showMessage('Test page printed successfully!', 'success');
            refreshStatus();
        }
    } catch (error) {
        showMessage(`Print error: ${error.message}`, 'error');
    }
}

async function updateSettings() {
    const intensity = parseInt(document.getElementById('intensity').value);
    const ditherMethod = document.getElementById('dither-method').value;

    try {
        showMessage('Updating settings...', 'info');
        const result = await apiCall('/api/settings', 'POST', {
            intensity: intensity,
            dither_method: ditherMethod
        });

        if (result.success) {
            showMessage('Settings updated successfully!', 'success');
        }
    } catch (error) {
        showMessage(`Settings error: ${error.message}`, 'error');
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl+Enter to print text
    if (event.ctrlKey && event.key === 'Enter') {
        const activeElement = document.activeElement;
        if (activeElement.id === 'print-text') {
            printText();
            event.preventDefault();
        }
    }
});
