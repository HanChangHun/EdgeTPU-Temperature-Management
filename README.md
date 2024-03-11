# EdgeTPU-Temperature-Management

## Coral Dev Board Services for Startup

1. Creating files in /etc/systemd/system/set-permissions.service

    ```sh
    [Unit]
    Description=Set permissions on boot and CPU governor on boot

    [Service]
    Type=oneshot
    ExecStart=/bin/sh -c ' \
    echo "Set permission about fan"; \
    chmod a+w /sys/devices/virtual/thermal/thermal_zone0/mode; \
    chmod a+w /sys/devices/platform/gpio_fan/hwmon/hwmon0/fan1_target; \
    chmod a+w /sys/devices/virtual/thermal/thermal_zone0/trip_point_4_temp; \
    echo "Set permission about TPU frequency"; \
    chmod a+w /sys/class/apex/apex_0/temp_poll_interval; \
    echo 10 > /sys/class/apex/apex_0/temp_poll_interval; \
    chmod a+w /sys/class/apex/apex_0/trip_point0_temp; \
    chmod a+w /sys/class/apex/apex_0/trip_point1_temp; \
    chmod a+w /sys/class/apex/apex_0/trip_point2_temp; \
    echo "Set permission about CPU frequency"; \
    chmod a+w /sys/devices/system/cpu/cpufreq/policy0/scaling_governor; \
    chmod a+w /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed; \
    '

    [Install]
    WantedBy=multi-user.target
    ```

2. Edit `/etc/init.d/cpufrequtils`

Starting from line 42, there is the following content.

```sh
...
ENABLE="true"

# **Change the GOVERNER**
# GOVERNOR="ondemand"
GOVERNOR="userspace"

MAX_SPEED="0"
MIN_SPEED="0"
...
```

3. Reload and start service

    ```sh
    sudo systemctl daemon-reload
    sudo systemctl enable set-permissions.service
    sudo systemctl start set-permissions.service
    ```

## Naming Conventions

This repository uses the following naming convention.

- CDB_XXX.sh
  - This is code that runs on the host, and internally executes commands for remote execution such as `ssh` or `scp`.
- CDB_XXX.py
  - This is Python code to run remotely. This code is not executed on the host.
- XXX.py
  - This code is executed by the Host. It mainly plays the following roles:
    - Data extract
      - All necessary preparations before measurement are also performed here.
      - ex. Turn on/off fan, adjust frequency
    - Data analysis
    - Data visualization

## Record Data

```sh
python3 src/record_data.py -u $USER -H $HOST -p $PORT -t $DURATION -P $POWER_NUM -i $INTERVAL -o result/$(date +%Y%m%d_%H%M%S)
```

## Visualize Result

```sh
python3 src/visualize.py -p path/to/result
```

## Inspect Result

```sh
python3 src/inspect_data.py -p path/to/result
```

## Analyze WCET

```sh
python3 src/analyze_wcet.py -u $USER -H $HOST -p $PORT \
                            -n $NUM_ITER -m path/to/model.tflite
```

## Measure Activity Factor

```sh
python3 src/measure_activity_factor.py -u username -H hostname -p port \
        -m path/to/model.tflite -e $WCET -U $UTIL -t $DURATION -P $POWER_NUM
```

## Issue Solutions

If the test stops in the middle and `libedgetpu.so` is occupied and subsequent tests cannot be run, perform the following on the Coral Dev Board.

```sh
fuser -k -9 /usr/lib/aarch64-linux-gnu/libedgetpu.so.1
```