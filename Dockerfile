ARG BUILD_FROM
FROM ${BUILD_FROM}

# Fix musl version conflict by explicitly upgrading musl first
RUN apk upgrade --no-cache musl

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    nodejs \
    npm \
    bluez \
    bluez-libs \
    dbus \
    build-base \
    cairo-dev \
    jpeg-dev \
    pango-dev \
    giflib-dev \
    pixman-dev \
    linux-headers

# Create working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY requirements.txt ./

# Install Node.js dependencies
RUN npm install --production

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY python_service/ ./python_service/
COPY node_service/ ./node_service/
COPY run.sh /

# Make run script executable
RUN chmod +x /run.sh

CMD ["/run.sh"]
