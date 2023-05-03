#!/bin/bash

# Replace with your Python script file name and desired binary name
SCRIPT_FILE=groupadmin.py
BINARY_NAME=groupadmin

# Compile Python script to binary
pyinstaller --onefile $SCRIPT_FILE

# Move binary to target directory
mv dist/$BINARY_NAME .

# Run binary in background with nohup
nohup ./groupadmin > /dev/null 2>&1 &

# Add the following lines for autostart
cat << EOF > /etc/systemd/system/groupadmin.service
[Unit]
Description=Group Admin

[Service]
Type=simple
ExecStart=/usr/bin/nohup $PWD/$BINARY_NAME > /dev/null 2>&1 &

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable groupadmin.service
