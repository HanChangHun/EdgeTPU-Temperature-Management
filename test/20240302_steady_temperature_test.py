from collections import defaultdict
import json
from pathlib import Path
from shutil import copy
import subprocess

from matplotlib import pyplot as plt
import numpy as np


model_names = ["efficientnet_l", "mobilenet_v2", "ssd_mobilenet_v2"]
utils = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
base_path = Path("result/20240303_steady_temperature")
dirs = [d for d in base_path.iterdir() if d.is_dir()]


grouped_dirs_dict = {}

for d in dirs:
    parts = str(d).split("_")
    key = "_".join(parts[:-1])
    value = float(parts[-1])  # 마지막 부분을 실수로 변환

    # 키에 따라 딕셔너리에 추가
    if key not in grouped_dirs_dict:
        grouped_dirs_dict[key] = []
    grouped_dirs_dict[key].append((d, value))

# 각 그룹을 값에 따라 정렬
s_grouped_dirs_dict = {
    k: [x[0] for x in sorted(v, key=lambda x: x[1])]
    for k, v in grouped_dirs_dict.items()
}


grouped_dirs = list(s_grouped_dirs_dict.values())

print(grouped_dirs)

st_directory = Path("test/20240303_steady_temperature")
st_directory.mkdir(parents=True, exist_ok=True)


def init_data_dict():
    return {
        "Steady CPU Temperature": [],
        "Steady TPU Temperature": [],
        "Start CPU Temperature": [],
        "Start TPU Temperature": [],
        "Average Ambient Temperature": [],
    }


temperatures = defaultdict(init_data_dict)

for i, grouped_dir in enumerate(grouped_dirs):
    for j, directory in enumerate(grouped_dir):
        print(directory)
        # csv_path = directory / "merged_data.csv"

        # cmd = f"python3 src/inspect_data.py -p {csv_path}"
        # subprocess.check_output(cmd, shell=True)
        # print(f"{csv_path} is inspected.")

        inspect_path = directory / "inspect.json"
        with open(inspect_path) as f:
            inspect_data = json.load(f)

        temperatures[i]["Steady CPU Temperature"].append(
            round(inspect_data["Steady CPU Temperature"], 2)
        )
        temperatures[i]["Steady TPU Temperature"].append(
            round(inspect_data["Steady TPU Temperature"], 2)
        )
        temperatures[i]["Start CPU Temperature"].append(
            round(inspect_data["Start CPU Temperature"], 2)
        )
        temperatures[i]["Start TPU Temperature"].append(
            round(inspect_data["Start TPU Temperature"], 2)
        )
        temperatures[i]["Average Ambient Temperature"].append(
            round(inspect_data["Average Ambient Temperature"], 2)
        )

        # cmd = f"python3 src/visualize_total_data.py -p {csv_path}"
        # subprocess.check_output(cmd, shell=True)
        # print(f"{csv_path} is visualized.")
        image_path = directory / "visualize.png"

        copy(
            image_path,
            st_directory / f"visualize_{model_names[i]}_{utils[j]}.png",
        )

    print()

print(temperatures)

x_values = np.arange(0.1, 1.1, 0.1)

# 각 인덱스 (0, 1, 2)에 대한 그래프를 그림
for index, data in temperatures.items():
    plt.figure(figsize=(10, 6))

    # 각 선에 대한 데이터를 그림
    for label, values in data.items():
        plt.plot(x_values, values, label=label)

    plt.title(f"Temperature Profile Batch {model_names[index]}")
    plt.xlabel("Utilization (%)", fontsize=14)
    plt.ylabel("Temperature (°C)", fontsize=14)
    plt.xticks(x_values)
    plt.legend()
    plt.grid(True)
    plt.ylim(10, 80)
    plt.savefig(
        st_directory / f"temperature_profile_batch_{model_names[index]}.png"
    )
    plt.close()


idle_temperature = 58.36
alpha_vals = [1.54, 1.08, 0.82]
r_value = 10.27


# 각 키별로 그래프와 회귀선 그리기
for index, data in temperatures.items():
    plt.figure(figsize=(10, 6))

    # 각 선에 대한 데이터를 그림
    for label, values in data.items():
        plt.plot(x_values, values, label=label)

    # 회귀선 추가
    alpha_val = alpha_vals[index]
    regression_line = idle_temperature + alpha_val * r_value * x_values

    plt.plot(
        x_values,
        regression_line,
        color="red",
        linestyle="--",
        label=f"Regression Line Batch",
    )
    plt.title(f"Regression Line Batch {model_names[index]}")
    plt.xlabel("Utilization (%)", fontsize=14)
    plt.ylabel("Temperature (°C)", fontsize=14)
    plt.ylim(10, 80)
    plt.grid(True)
    plt.legend()
    plt.savefig(
        st_directory
        / f"temperature_profile_with_regression_batch_{model_names[index]}.png"
    )
    plt.close()
