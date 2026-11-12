# ---- Stage 1: Clone the webui-aria2 repository ----
FROM alpine/git AS clone-subxtract

# Clone the subxtract repository
RUN git clone https://github.com/aminelazz/subxtract.git /subxtract

# ---- Stage 2: Build the final image ----
# Base image (Python 3.10 on Alpine 3.22)
FROM python:3.10-alpine3.22

# Set ENV variables
ENV DISCORD_TOKEN=
ENV APP_ID=
ENV ARIA2_RPC_PORT=6800
ENV USERID=1000
ENV GROUPID=1000

# Set arguments
ARG ARIA2_RPC_HOST=http://localhost
ARG ARIA2_RPC_SECRET=YOUR_RPC_SECRET

ARG TEMP_DIR=./data/temp
ARG DOWNLOAD_DIR=./data/temp/downloads
ARG EXTRACT_DIR=./data/temp/extracted
ARG SCHEMAS_DIR=./schemas

ARG ALLOWED_CHANNELS_FILE=./data/allowed_channels.json
ARG CURRENT_DL_FILE=./data/current_download.json
ARG QUEUE_FILE=./data/queue.json
ARG TUNNEL_URL_FILE=./data/cloudflare_tunnel_url.txt

# Install aria2 and optional utilities
RUN apk add --no-cache aria2 mkvtoolnix mediainfo

# Copy subxtract from the clone stage
COPY --from=clone-subxtract /subxtract /subxtract

# Expose aria2 RPC port
EXPOSE 6800

# Set working directory
WORKDIR /subxtract

# Populate .env file
RUN cat > .env <<EOF
DISCORD_TOKEN=${DISCORD_TOKEN}
APP_ID=${APP_ID}
ARIA2_RPC_HOST=${ARIA2_RPC_HOST}
ARIA2_RPC_PORT=${ARIA2_RPC_PORT}
ARIA2_RPC_SECRET=${ARIA2_RPC_SECRET}
TEMP_DIR=${TEMP_DIR}
DOWNLOAD_DIR=${DOWNLOAD_DIR}
EXTRACT_DIR=${EXTRACT_DIR}
SCHEMAS_DIR=${SCHEMAS_DIR}
ALLOWED_CHANNELS_FILE=${ALLOWED_CHANNELS_FILE}
CURRENT_DL_FILE=${CURRENT_DL_FILE}
QUEUE_FILE=${QUEUE_FILE}
TUNNEL_URL_FILE=${TUNNEL_URL_FILE}
EOF

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create entrypoint script to handle dynamic user creation
RUN cat > /entrypoint.sh <<'EOF'
#!/bin/sh
set -e

# Create group if it does not exist
if ! getent group ${GROUPID} > /dev/null 2>&1; then
    addgroup -g ${GROUPID} subxtractgroup
else
    groupmod -g ${GROUPID} subxtractgroup 2>/dev/null || true
fi

# Create user if it does not exist
if ! getent passwd ${USERID} > /dev/null 2>&1; then
    adduser -D -u ${USERID} -G subxtractgroup subxtractuser
else
    usermod -u ${USERID} -g ${GROUPID} subxtractuser 2>/dev/null || true
fi

# Fix ownership of application directories
chown -R subxtractuser:subxtractgroup /subxtract

# Execute command as subxtractuser
exec su-exec subxtractuser "$@"
EOF
RUN chmod +x /entrypoint.sh

# Install su-exec for safer user switching
RUN apk add --no-cache su-exec

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/subxtract/start.sh"]
