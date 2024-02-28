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
    chmod a+w /sys/class/apex/apex_0/trip_point0_temp; \
    chmod a+w /sys/class/apex/apex_0/trip_point1_temp; \
    chmod a+w /sys/class/apex/apex_0/trip_point2_temp; \
    echo "Set permission about CPU frequency"; \
    echo userspace > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor; \
    chmod a+w /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed \
    '

    [Install]
    WantedBy=multi-user.target
    ```

2. Reload and start service

    ```sh
    sudo systemctl daemon-reload
    sudo systemctl enable set-permissions.service
    sudo systemctl start set-permissions.service
    ```

## Record Data

```sh
python3 src/record_data.py -u username -H hostname -p port -P power_num -t time
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
python3 src/analyze_wcet.py -u username -H hostname -p port -P power_num \
                            -i num_iter -m path/to/model.tflite
```
