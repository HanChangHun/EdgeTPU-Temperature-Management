#!/bin/bash

# 기본 측정 시간을 설정합니다. 인자가 제공되지 않을 경우 사용됩니다.
DUR=10
PORT=22 # 기본 포트를 22로 설정
USER=""
HOST=""

# 옵션과 인자를 처리합니다.
while getopts "t:p:u:h:" opt; do
    case $opt in
    t) DUR=$OPTARG ;;
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
    echo "Usage: $0 -t <DUR> -p <PORT> -u <USER> -h <HOST>"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p result/$TIMESTAMP
FILE_NAME="result/$(date +%Y%m%d_%H%M%S)/proc_temp_data.csv"

scp -P $PORT ./src/CDB_read_proc_temperature.py \
    $USER@$HOST:/tmp/CDB_read_proc_temperature.py

ssh -p $PORT $USER@$HOST "python3 /tmp/CDB_read_proc_temperature.py -t $DUR"

ssh -p $PORT $USER@$HOST \
    "ls -t /tmp/result/proc_temp_data_*.csv | head -n 1" |
    xargs -I {} scp -P $PORT $USER@$HOST:{} \
        "$FILE_NAME"

echo $TIMESTAMP
