import json
from pathlib import Path
from datetime import datetime
import subprocess
from shutil import copy

from matplotlib import pyplot as plt
import numpy as np


# 시작 및 종료 날짜 설정
start_date = datetime.strptime("20240228_215915", "%Y%m%d_%H%M%S")
end_date = datetime.strptime("20240229_074100", "%Y%m%d_%H%M%S")

# 디렉토리 리스트 불러오기
base_path = Path("result/20240229_steady_temperature")
directories = [d for d in base_path.iterdir() if d.is_dir()]

# 필터링 및 정렬
filtered_dirs = []
for directory in directories:
    dir_name = directory.name
    try:
        dir_time = datetime.strptime(dir_name, "%Y%m%d_%H%M%S")
        if start_date <= dir_time <= end_date:
            filtered_dirs.append(directory)
    except ValueError:
        # 디렉토리 이름이 지정된 형식에 맞지 않으면 무시
        continue

# 시간 순으로 정렬
sorted_dirs = sorted(
    filtered_dirs, key=lambda x: datetime.strptime(x.name, "%Y%m%d_%H%M%S")
)

# 10개씩 묶어서 작업 (예시)
batches = [sorted_dirs[i : i + 10] for i in range(0, len(sorted_dirs), 10)]


st_directory = Path("test/20240229_steady_temperature")
st_directory.mkdir(parents=True, exist_ok=True)

temperatures = {}
# 결과 출력 (예시로 첫 번째 배치의 디렉토리 이름들을 출력)
for i, batch in enumerate(batches):
    temperatures[f"{i}"] = []
    for j, directory in enumerate(batch):
        print(directory)
        csv_path = directory / "merged_data.csv"

        # cmd = f"python3 src/inspect_data.py -p {csv_path}"
        # subprocess.check_output(cmd, shell=True)
        # print(f"{csv_path} is inspected.")
        inspect_path = directory / "result.json"
        with open(inspect_path) as f:
            inspect_data = json.load(f)

        temperature = round(
            max(
                inspect_data["CPU Temperature"],
                inspect_data["TPU Temperature"],
            ),
            2,
        )
        temperatures[f"{i}"].append(temperature)

        # cmd = f"python3 src/visualize.py -p {csv_path}"
        # subprocess.check_output(cmd, shell=True)
        # print(f"{csv_path} is visualized.")
        # image_path = directory / "visualize.png"

        # copy(image_path, st_directory / f"visualize_{i}_{j}.png")

    print()

print(temperatures)

# x축 값 생성 (1.0부터 0.1까지 0.1씩 감소)
x_values = np.arange(1.0, 0, -0.1)
alpha_vals = [0.87, 1.33, 0.8]
r_value = 10.27
idle_temperature = 58.36

# 각 키별로 그래프 그리기
for key, temps in temperatures.items():
    plt.figure(figsize=(8, 8))
    plt.plot(
        x_values[: len(temps)],
        temps,
        marker="o",
        linestyle="-",
        label=f"Batch {key}",
    )
    plt.xlabel("Utilization (%)", fontsize=14)
    plt.ylabel("Temperature (°C)", fontsize=14)
    plt.grid(True)
    plt.ylim(55, 70)
    plt.savefig(st_directory / f"temperature_profile_batch_{key}.png")
    plt.close()

# 각 키별로 그래프와 회귀선 그리기
for i, (key, temps) in enumerate(temperatures.items()):
    plt.figure(figsize=(8, 8))
    # 원래의 온도 데이터 플롯
    plt.plot(
        x_values[: len(temps)],
        temps,
        marker="o",
        linestyle="-",
        label=f"Batch {key}",
    )
    # 회귀선 추가
    alpha_val = alpha_vals[i]
    regression_line = (
        idle_temperature + alpha_val * r_value * x_values[: len(temps)]
    )
    plt.plot(
        x_values[: len(temps)],
        regression_line,
        color="red",
        linestyle="--",
        label=f"Regression Line Batch {key}",
    )
    plt.xlabel("Utilization (%)", fontsize=14)
    plt.ylabel("Temperature (°C)", fontsize=14)
    plt.ylim(55, 70)
    plt.grid(True)
    plt.savefig(
        st_directory / f"temperature_profile_with_regression_batch_{key}.png"
    )
    plt.close()
