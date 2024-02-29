#!/bin/bash

while getopts u:H:p: flag; do
    case "${flag}" in
    u) USER=${OPTARG} ;;
    H) HOST=${OPTARG} ;;
    p) PORT=${OPTARG} ;;
    esac
done

# 인자 확인
if [ -z "$USER" ] || [ -z "$HOST" ]; then
    echo "Usage: $0 -u <user> -H <host> [-p <port>]"
    exit 1
fi

# CPU와 TPU 주파수 설정
CPU_FREQS=(0.5 1.0 1.5)
TPU_FREQS=(62.5 125 250 500)
UTIL_VALUE=1.0

# 주파수 변경하면서 모델 실행
for CPU_FREQ in "${CPU_FREQS[@]}"; do
    for TPU_FREQ in "${TPU_FREQS[@]}"; do
        # 주파수 변경
        echo "Changing frequency: CPU = $CPU_FREQ GHz, TPU = $TPU_FREQ MHz"
        ./src/CDB_change_frequency.sh -u $USER -h $HOST -p $PORT -t $TPU_FREQ -c $CPU_FREQ

        # 모델 실행
        echo "Running model with CPU: $CPU_FREQ GHz, TPU: $TPU_FREQ MHz"
        python3 src/measure_activity_factor.py -u $USER -H $HOST -p $PORT \
            -m "test_data/mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite" \
            -e 3.8 -U $UTIL_VALUE -t 60 -P 1
        sleep 60

        # Run the second model
        python3 src/measure_activity_factor.py -u $USER -H $HOST -p $PORT \
            -m "test_data/efficientnet-edgetpu-L_quant_edgetpu.tflite" \
            -e 25.98 -U $UTIL_VALUE -t 60 -P 1
        sleep 60

        # Run the third model
        python3 src/measure_activity_factor.py -u $USER -H $HOST -p $PORT \
            -m "test_data/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite" \
            -e 12.75 -U $UTIL_VALUE -t 60 -P 1
        sleep 60
    done
done
