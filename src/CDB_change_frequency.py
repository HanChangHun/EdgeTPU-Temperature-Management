import argparse
from pathlib import Path
import os
from stat import S_IWOTH

#############################
# Please refer to the `README.md` file for permission settings.
#############################

DEVICE_PATH = Path("/sys/class/apex/apex_0/")
TRIP_POINTS_PATHS = [DEVICE_PATH / f"trip_point{i}_temp" for i in range(3)]
POLL_INTERVAL_PATH = DEVICE_PATH / "temp_poll_interval"
CPU_FREQ_PATH = "/sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed"


def check_tpu_writable():
    for path in TRIP_POINTS_PATHS:
        if not path.is_file():
            raise FileNotFoundError(f"{path} does not exist.")

        file_stat = path.stat()
        writable_by_others = file_stat.st_mode & S_IWOTH

        if not writable_by_others:
            raise PermissionError(f"{path} is not writable by others.")

    if not POLL_INTERVAL_PATH.is_file():
        raise FileNotFoundError(f"{POLL_INTERVAL_PATH} does not exist.")

    file_stat = POLL_INTERVAL_PATH.stat()
    writable_by_others = file_stat.st_mode & S_IWOTH

    if not writable_by_others:
        raise PermissionError(
            f"{POLL_INTERVAL_PATH} is not writable by others."
        )

    with open(POLL_INTERVAL_PATH, "w") as f:
        f.write("1000")


def write_values(path, trip_points):
    with open(path, "w") as f:
        f.write(str(trip_points))


def change_trip_points(t1, t2, t3):
    write_values(TRIP_POINTS_PATHS[2], 110000)
    write_values(TRIP_POINTS_PATHS[1], 105000)
    write_values(TRIP_POINTS_PATHS[0], 100000)

    for temp, path in zip([t1, t2, t3], TRIP_POINTS_PATHS):
        write_values(path, temp)


def change_tpu_frequency(frequency):
    trip_points = {
        500: (93000, 94000, 95000),
        250: (5000, 94000, 95000),
        125: (5000, 6000, 95000),
        62.5: (5000, 6000, 7000),
    }

    if frequency in trip_points:
        change_trip_points(*trip_points[frequency])
        print(f"Changed TPU frequency to {frequency} MHz.")
    else:
        raise ValueError(f"{frequency} is not a valid frequency.")


def change_cpu_frequency(frequency):
    frequency_in_khz = int(frequency * 1000 * 1000)  # GHz to kHz
    write_values(CPU_FREQ_PATH, frequency_in_khz)
    print(f"Changed CPU frequency to {frequency} GHz.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--tpu_freq", type=float, default=500)
    parser.add_argument("-c", "--cpu_freq", type=float, default=1.5)
    args = parser.parse_args()

    check_tpu_writable()
    change_tpu_frequency(args.tpu_freq)
    change_cpu_frequency(args.cpu_freq)
