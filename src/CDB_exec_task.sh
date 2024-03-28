#!/bin/bash

USER="mendel" # Set default user to "mendel"
HOST=
PORT=22 # Set default port to 22
MODEL_PATH=
WCET=
U_RATE=
DUR=10

# 옵션과 인자를 처리합니다.
while getopts "u:H:p:m:e:U:t:" opt; do
    case $opt in
    u) USER=$OPTARG ;;
    H) HOST=$OPTARG ;;
    p) PORT=$OPTARG ;;
    m) MODEL_PATH=$OPTARG ;;
    e) WCET=$OPTARG ;;
    U) U_RATE=$OPTARG ;;
    t) DUR=$OPTARG ;;
    \?)
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    esac
done

if [ -z "$HOST" ] || [ -z "$MODEL_PATH" ]; then
    echo "Usage: $0 -u <USER> -H <HOST> -p <PORT> -m <MODEL_PATH> -t <DURATION> \
                    -e <WCET> -U <UTILIZATION_RATE>"
    exit 1
fi

ssh -p $PORT $USER@$HOST "mkdir -p /tmp/test_data"

scp -q -P $PORT ./src/CDB_exec_task.py \
    $USER@$HOST:/tmp/CDB_exec_task.py
scp -q -P $PORT $MODEL_PATH $USER@$HOST:/tmp/$MODEL_PATH

ssh -p $PORT $USER@$HOST "python3 /tmp/CDB_exec_task.py -m /tmp/$MODEL_PATH -e $WCET -U $U_RATE -t $DUR"
