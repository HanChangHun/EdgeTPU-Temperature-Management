#!/bin/bash

USER="mendel"
HOST=""
PORT=22
TPU_FREQ=500 # [62.5, 125, 250, 500] are available
CPU_FREQ=1.5 # [0.5, 1.0, 1.5] are available

# Handles options and arguments.
while getopts "u:h:p:t:c:" opt; do
    case $opt in
    u) USER=$OPTARG ;;
    h) HOST=$OPTARG ;;
    p) PORT=$OPTARG ;;
    t) TPU_FREQ=$OPTARG ;;
    c) CPU_FREQ=$OPTARG ;;
    \?)
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    esac
done

if [ -z "$USER" ] || [ -z "$HOST" ]; then
    echo "Usage: $0  -u <USER> -h <HOST> -p <PORT> -t <TPU_FREQ> -c <CPU_FREQ>"
    exit 1
fi

scp -P $PORT ./src/CDB_change_frequency.py \
    $USER@$HOST:/tmp/CDB_change_frequency.py

ssh -p $PORT $USER@$HOST "python3 /tmp/CDB_change_frequency.py -t $TPU_FREQ -c $CPU_FREQ"

echo "TPU Frequency: $TPU_FREQ MHz, CPU Frequency: $CPU_FREQ GHz"
