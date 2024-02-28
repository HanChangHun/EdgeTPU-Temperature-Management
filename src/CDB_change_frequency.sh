#!/bin/bash

TPU_FREQ=500 # [62.5, 125, 250, 500] are available
CPU_FREQ=1.5 # [0.5, 1.0, 1.5] are available
PORT=22
USER=""
HOST=""

# Handles options and arguments.
while getopts "t:c:p:u:h:" opt; do
    case $opt in
    t) TPU_FREQ=$OPTARG ;;
    c) CPU_FREQ=$OPTARG ;;
    p) PORT=$OPTARG ;;
    u) USER=$OPTARG ;;
    h) HOST=$OPTARG ;;
    \?)
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    esac
done

if [ -z "$USER" ] || [ -z "$HOST" ]; then
    echo "Usage: $0 -t <TPU_FREQ> -c <CPU_FREQ> -p <PORT> -u <USER> -h <HOST>"
    exit 1
fi

scp -P $PORT ./src/CDB_change_frequency.py \
    $USER@$HOST:/tmp/CDB_change_frequency.py

ssh -p $PORT $USER@$HOST "python3 /tmp/CDB_change_frequency.py -t $TPU_FREQ -c $CPU_FREQ"
