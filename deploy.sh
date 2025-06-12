#!/bin/bash

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install required system packages
sudo apt-get install -y python3-pip python3-venv portaudio19-dev

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create systemd service file
sudo tee /etc/systemd/system/jarvis.service << EOF
[Unit]
Description=Jarvis AI Assistant
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python3 backend/feature.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable jarvis
sudo systemctl start jarvis

echo "Jarvis has been deployed and started as a service!"
echo "Check status with: sudo systemctl status jarvis"
echo "View logs with: sudo journalctl -u jarvis -f" 