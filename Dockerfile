ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install system dependencies with musl upgrade to fix version conflict
RUN apk add --no-cache --upgrade \
    musl \
    python3 \
    py3-pip \
    build-base \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev

# Create working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt ./

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY python_service/ ./python_service/
COPY run.sh /

# Make run script executable
RUN chmod +x /run.sh

CMD ["/run.sh"]
