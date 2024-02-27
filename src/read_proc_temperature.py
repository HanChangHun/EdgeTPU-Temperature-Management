import argparse
import csv
from pathlib import Path
import time


def read_temperature(file_path):
    with open(file_path, "r") as file:
        return int(file.read()) / 1000


def main():
    # 인자 파서를 생성합니다.
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "-t", dest="dur", type=int, default=10, help="Duration in seconds"
    )

    # 인자를 파싱합니다.
    args = parser.parse_args()

    output_file = Path(
        f"/tmp/result/proc_temp_data_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    )
    if not output_file.parent.exists():
        output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", newline="") as f:
        fieldnames = [
            "Timestamp",
            "CPU Temperature",
            "TPU Temperature",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()

        for _ in range(args.dur):
            cpu_temp = read_temperature(
                "/sys/class/thermal/thermal_zone0/temp"
            )
            tpu_temp = read_temperature("/sys/class/apex/apex_0/temp")
            timestamp = int(time.time() * 1000)
            writer.writerow(
                {
                    "Timestamp": timestamp,
                    "CPU Temperature": cpu_temp,
                    "TPU Temperature": tpu_temp,
                }
            )
            time.sleep(1)


if __name__ == "__main__":
    main()
