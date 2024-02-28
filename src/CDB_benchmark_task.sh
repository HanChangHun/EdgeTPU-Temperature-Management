#!/bin/bash

USER="mendel" # Set default user to "mendel"
HOST=""
PORT=22 # Set default port to 22
CPU_FREQ=1.5
TPU_FREQ=500
MODEL_PATH=""
OUTPUT_NAME=""
NUM_ITER=100

# 옵션과 인자를 처리합니다.
while getopts "u:h:p:c:t:m:o:n:" opt; do
    case $opt in
    u) USER=$OPTARG ;;
    h) HOST=$OPTARG ;;
    p) PORT=$OPTARG ;;
    c) CPU_FREQ=$OPTARG ;;
    t) TPU_FREQ=$OPTARG ;;
    m) MODEL_PATH=$OPTARG ;;
    o) OUTPUT_NAME=$OPTARG ;;
    n) NUM_ITER=$OPTARG ;;
    \?)
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    esac
done

if [ -z "$HOST" ] || [ -z "$MODEL_PATH" ] || [ -z "$OUTPUT_NAME" ]; then
    echo "Usage: $0 -u <USER> -h <HOST> -p <PORT> -c <CPU_FREQ> -t <TPU_FREQ> \
                    -m <MODEL_PATH> -o <OUTPUT_NAME> -n <NUM_ITER>"
    exit 1
fi

mkdir -p result/benchmark
OUTPUT_CSV_PATH="result/benchmark/$OUTPUT_NAME"

# TODO: I think I need to create the directory earlier.
ssh -p $PORT $USER@$HOST "mkdir -p /tmp/result/benchmark"
ssh -p $PORT $USER@$HOST "mkdir -p /tmp/test_data"

scp -P $PORT ./src/CDB_benchmark_task.py \
    $USER@$HOST:/tmp/CDB_benchmark_task.py
scp -P $PORT $MODEL_PATH $USER@$HOST:/tmp/$MODEL_PATH

./src/CDB_change_frequency.sh -u $USER -h $HOST -p $PORT -c $CPU_FREQ -t $TPU_FREQ
./src/CDB_disable_fan.sh -u $USER -h $HOST -p $PORT


ssh -p $PORT $USER@$HOST "python3 /tmp/CDB_benchmark_task.py -m /tmp/$MODEL_PATH -n $NUM_ITER -o $OUTPUT_NAME"
scp -P $PORT $USER@$HOST:/tmp/result/benchmark/$OUTPUT_NAME $OUTPUT_CSV_PATH

# ./src/CDB_enable_fan.sh -u $USER -h $HOST -p $PORT
# ./src/CDB_change_frequency.sh -u $USER -h $HOST -p $PORT
