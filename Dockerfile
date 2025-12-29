ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install system dependencies with musl upgrade to fix version conflict
RUN apk add --no-cache --upgrade \
    musl \
    python3 \
    py3-pip \
    nodejs \
    npm \
    bluez \
    bluez-deprecated \
    bluez-libs \
    dbus \
    dbus-x11 \
    build-base \
    cairo-dev \
    jpeg-dev \
    pango-dev \
    giflib-dev \
    pixman-dev \
    linux-headers && \
    echo "=== Checking for bluetoothd ===" && \
    which bluetoothd || echo "bluetoothd not found in PATH"

# Create working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY requirements.txt ./

# Install Node.js dependencies
RUN npm install --production && \
    echo "=== Installed packages ===" && \
    npm list --depth=0 || true && \
    echo "=== Checking node_modules ===" && \
    ls -la node_modules/ | head -20 && \
    echo "=== Checking @stoprocent/noble ===" && \
    ls -la node_modules/@stoprocent/noble 2>/dev/null || echo "Noble not found in expected location"

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY python_service/ ./python_service/
COPY node_service/ ./node_service/
COPY run.sh /

# Rebuild native modules to ensure they work in the container environment
RUN echo "=== Rebuilding native modules ===" && \
    npm rebuild && \
    echo "=== Verifying canvas ===" && \
    node -e "require('canvas'); console.log('canvas OK')" && \
    echo "=== Verifying @stoprocent/noble ===" && \
    node -e "require('@stoprocent/noble'); console.log('noble OK')" || echo "Noble verification failed"

# Make run script executable
RUN chmod +x /run.sh

CMD ["/run.sh"]
