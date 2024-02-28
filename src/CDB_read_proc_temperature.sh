#!/bin/bash

USER="mendel" # Set default user to "mendel"
HOST=""
PORT=22 # Set default port to 22
DUR=10

# 옵션과 인자를 처리합니다.
while getopts "u:h:p:t:" opt; do
    case $opt in
    u) USER=$OPTARG ;;
    h) HOST=$OPTARG ;;
    p) PORT=$OPTARG ;;
    t) DUR=$OPTARG ;;
    \?)
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    esac
done

if [ -z "$USER" ] || [ -z "$HOST" ]; then
    echo "Usage: $0 -u <USER> -h <HOST> -p <PORT> -t <DUR>"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p result/$TIMESTAMP
FILE_NAME="result/$(date +%Y%m%d_%H%M%S)/proc_temp_data.csv"

scp -P $PORT ./src/CDB_read_proc_temperature.py \
    $USER@$HOST:/tmp/CDB_read_proc_temperature.py

./src/CDB_disable_fan.sh -u $USER -h $HOST -p $PORT

ssh -p $PORT $USER@$HOST "python3 /tmp/CDB_read_proc_temperature.py -t $DUR"

./src/CDB_enable_fan.sh -u $USER -h $HOST -p $PORT

ssh -p $PORT $USER@$HOST \
    "ls -t /tmp/result/proc_temp_data_*.csv | head -n 1" |
    xargs -I {} scp -P $PORT $USER@$HOST:{} \
        "$FILE_NAME"

echo $TIMESTAMP
