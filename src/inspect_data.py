import pandas as pd
import argparse
import json
from pathlib import Path


def rolling_median(data, column_name, window_size):
    # 롤링 윈도우를 사용하여 각 윈도우의 특정 백분위수 값을 계산
    rolling_quantile = (
        data[column_name].rolling(window=window_size).quantile(0.5)
    )
    # 계산된 백분위수 값들 중 최대값을 steady temperature로 선정
    return rolling_quantile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--csv_path",
        type=str,
        required=True,
        help="Path to CSV file to analyze",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    result_json_path = csv_path.parent / "inspect.json"

    data = pd.read_csv(csv_path)
    averages = data.mean()
    avg_data_dict = averages.to_dict()
    result_dict = {
        "Average CPU Temperature": avg_data_dict["CPU Temperature"],
        "Average TPU Temperature": avg_data_dict["TPU Temperature"],
        "Average Ambient Temperature": avg_data_dict["Ambient Temperature"],
        "Average Power": avg_data_dict["Power"],
    }

    # Rolling window settings
    cpu_rolling_median = rolling_median(data, "CPU Temperature", 10)
    tpu_rolling_median = rolling_median(data, "TPU Temperature", 10)
    start_cpu_temp = cpu_rolling_median.min()
    start_tpu_temp = tpu_rolling_median.min()
    steady_cpu_temp = cpu_rolling_median.max()
    steady_tpu_temp = tpu_rolling_median.max()
    result_dict["Start CPU Temperature"] = start_cpu_temp
    result_dict["Start TPU Temperature"] = start_tpu_temp
    result_dict["Steady CPU Temperature"] = steady_cpu_temp
    result_dict["Steady TPU Temperature"] = steady_tpu_temp

    # Calculate Thermal Resistance for `idle state` of CPU and TPU
    result_dict["R_CPU"] = (
        averages["CPU Temperature"] - averages["Ambient Temperature"]
    ) / averages["Power"]
    result_dict["R_TPU"] = (
        averages["TPU Temperature"] - averages["Ambient Temperature"]
    ) / averages["Power"]

    with open(result_json_path, "w") as f:
        json.dump(result_dict, f, indent=4)


if __name__ == "__main__":
    main()
