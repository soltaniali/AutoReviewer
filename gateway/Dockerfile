FROM python:3.10-slim
# Bypass any Windows VPN/Proxy settings (like v2ray or shadowsocks) 
# that Docker Desktop automatically injects into the container. 
# Proxying to "localhost" fails inside Docker because it looks inside the container itself.
ENV HTTP_PROXY="" \
    HTTPS_PROXY="" \
    http_proxy="" \
    https_proxy="" \
    NO_PROXY="*"

# Install required system dependencies for C-extensions (like Cython needed by mlflow)
RUN . /etc/os-release && \
    echo "deb http://mirror.arvancloud.ir/debian $VERSION_CODENAME main" > /etc/apt/sources.list && \
    echo "deb http://mirror.arvancloud.ir/debian-security $VERSION_CODENAME-security main" >> /etc/apt/sources.list && \
    rm -f /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get -y install --no-install-recommends gcc build-essential g++ && rm -rf /var/lib/apt/lists/*

# Install mlflow with gateway dependencies using a different free mirror (ArvanCloud) to bypass Runflare API limits
RUN pip install --proxy="" --no-cache-dir -i https://pypi.arvancloud.ir/simple --upgrade pip && \
    pip install --proxy="" --no-cache-dir -i https://pypi.arvancloud.ir/simple mlflow[gateway]

# Expose the port the gateway runs on
EXPOSE 5000

# Start the gateway
CMD ["mlflow", "gateway", "start", "--config-path", "/gateway/config.yaml", "--port", "5000", "--host", "0.0.0.0"]
