import pandas as pd
import argparse
import json
from pathlib import Path


def calculate_steady_temperature(
    data, column_name, window_size, quantile_value
):
    # 롤링 윈도우를 사용하여 각 윈도우의 특정 백분위수 값을 계산
    rolling_quantile = (
        data[column_name].rolling(window=window_size).quantile(quantile_value)
    )
    # 계산된 백분위수 값들 중 최대값을 steady temperature로 선정
    steady_temperature = rolling_quantile.max()
    return steady_temperature


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
    result_json_path = csv_path.parent / "result.json"

    data = pd.read_csv(csv_path)
    averages = data.mean()
    results = averages.to_dict()

    # Rolling window settings
    window_size = 10
    quantile_value = 0.5
    steady_cpu_temp = calculate_steady_temperature(
        data, "CPU Temperature", window_size, quantile_value
    )
    steady_tpu_temp = calculate_steady_temperature(
        data, "TPU Temperature", window_size, quantile_value
    )
    results["Steady CPU Temperature"] = steady_cpu_temp
    results["Steady TPU Temperature"] = steady_tpu_temp

    # Calculate Thermal Resistance for `idle state` of CPU and TPU
    results["R_CPU"] = (
        averages["CPU Temperature"] - averages["Ambient Temperature"]
    ) / averages["Power"]
    results["R_TPU"] = (
        averages["TPU Temperature"] - averages["Ambient Temperature"]
    ) / averages["Power"]

    with open(result_json_path, "w") as f:
        json.dump(results, f, indent=4)


if __name__ == "__main__":
    main()
