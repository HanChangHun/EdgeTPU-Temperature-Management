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

# Execute instructions according to the range of UTIL values
for UTIL in {10..1}; do
    UTIL_VALUE=$(echo "scale=1; $UTIL / 10" | bc)

    # Run your first model
    echo "Running first model with UTIL: $UTIL_VALUE"
    python3 src/measure_activity_factor.py -u $USER -H $HOST -p $PORT \
        -m "test_data/mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite" \
        -e 3.8 -U $UTIL_VALUE -t 900 -P 1
    sleep 300

    # Run the second model
    echo "Running second model with UTIL: $UTIL_VALUE"
    python3 src/measure_activity_factor.py -u $USER -H $HOST -p $PORT \
        -m "test_data/efficientnet-edgetpu-L_quant_edgetpu.tflite" \
        -e 25.98 -U $UTIL_VALUE -t 900 -P 1
    sleep 300

    # Run the third model
    echo "Running third model with UTIL: $UTIL_VALUE"
    python3 src/measure_activity_factor.py -u $USER -H $HOST -p $PORT \
        -m "test_data/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite" \
        -e 12.75 -U $UTIL_VALUE -t 900 -P 1
    sleep 300
done
