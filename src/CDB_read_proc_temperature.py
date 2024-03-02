import argparse
import csv
from pathlib import Path
import time


def read_temperature(file_path):
    with open(file_path, "r") as file:
        return int(file.read()) / 1000


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t", "--dur", type=int, default=10, help="Duration in seconds"
    )
    parser.add_argument(
        "-i", "--interval", type=float, default=1.0, help="Duration in seconds"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="/tmp/result",
        help="Output file path",
    )

    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        fieldnames = [
            "Timestamp",
            "CPU Temperature",
            "TPU Temperature",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        start_time = time.time()
        total_iterations = int(args.dur / args.interval)

        for i in range(total_iterations):
            expected_time = start_time + i * args.interval
            now = time.time()

            # 현재 시간이 예상 시간을 넘었을 경우, 즉시 데이터를 기록
            if now < expected_time:
                time.sleep(expected_time - now)  # 정확한 시간까지 대기

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


if __name__ == "__main__":
    main()
