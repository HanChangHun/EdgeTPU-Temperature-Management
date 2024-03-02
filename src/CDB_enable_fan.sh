#!/bin/bash

USER="mendel" # Set default user to "mendel"
HOST=""
PORT=22 # Set default port to 22

# Handles options and arguments.
while getopts "u:H:p:" opt; do
    case $opt in
    u) USER=$OPTARG ;;
    H) HOST=$OPTARG ;;
    p) PORT=$OPTARG ;;
    \?)
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    esac
done

ssh -p $PORT $USER@$HOST "\
echo 'enabled' > /sys/devices/virtual/thermal/thermal_zone0/mode; \
echo 8600 > /sys/devices/platform/gpio_fan/hwmon/hwmon0/fan1_target"

echo "CDB Fan enabled"
