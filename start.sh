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