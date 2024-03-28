#!/bin/bash

USER="mendel" # Set default user to "mendel"
HOST=""
PORT=22 # Set default port to 22
DUR=10
INTERVAL=1.0
OUT_DIR="result"

# 옵션과 인자를 처리합니다.
while getopts "u:H:p:t:i:o:" opt; do
    case $opt in
    u) USER=$OPTARG ;;
    H) HOST=$OPTARG ;;
    p) PORT=$OPTARG ;;
    t) DUR=$OPTARG ;;
    i) INTERVAL=$OPTARG ;;
    o) OUT_DIR=$OPTARG ;;
    \?)
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    esac
done

if [ -z "$USER" ] || [ -z "$HOST" ]; then
    echo "Usage: $0 -u <USER> -H <HOST> -p <PORT> \
    -t <DUR> -i <INTERVAL> -o <OUT_DIR>"
    exit 1
fi

mkdir -p $OUT_DIR
OUTPUT_CSV_PATH="$OUT_DIR/proc_temp_data.csv"

scp -q -P $PORT ./src/CDB_read_proc_temperature.py \
    $USER@$HOST:/tmp/CDB_read_proc_temperature.py

ssh -p $PORT $USER@$HOST "python3 /tmp/CDB_read_proc_temperature.py \
                            -t $DUR -i $INTERVAL -o /tmp/$OUTPUT_CSV_PATH"

scp -q -P $PORT $USER@$HOST:/tmp/$OUTPUT_CSV_PATH $OUTPUT_CSV_PATH
