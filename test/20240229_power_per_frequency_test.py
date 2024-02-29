import json
from pathlib import Path
from datetime import datetime
import subprocess
from shutil import copy

from matplotlib import pyplot as plt
import numpy as np


# 시작 및 종료 날짜 설정
start_date = datetime.strptime("20240229_092207", "%Y%m%d_%H%M%S")
end_date = datetime.strptime("20240229_103540", "%Y%m%d_%H%M%S")

# 디렉토리 리스트 불러오기
base_path = Path("result/20240229_power_per_freq")
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

cpu_freqs = [0.5, 1.0, 1.5]
tpu_freqs = [62.5, 125, 250, 500]
task_names = ["MobileNet_v2", "EfficientNet-L", "SSD_MobileNet_v2"]
# 3개씩 묶기 (동일 TPU freq)
tpu_batches = [sorted_dirs[i : i + 3] for i in range(0, len(sorted_dirs), 3)]
# 4개씩 묶기 (동일 CPU freq)
cpu_batches = [tpu_batches[i : i + 4] for i in range(0, len(tpu_batches), 4)]

pf_directory = Path("test/20240229_power_per_freq")
pf_directory.mkdir(parents=True, exist_ok=True)

powers = {}
# 결과 출력 (예시로 첫 번째 배치의 디렉토리 이름들을 출력)
for i, batches in enumerate(cpu_batches):
    print(cpu_freqs[i])
    powers[f"{cpu_freqs[i]}"] = {}
    # temperatures[f"{i}"] = []
    for j, batch in enumerate(batches):
        print(tpu_freqs[j])
        powers[f"{cpu_freqs[i]}"][f"{tpu_freqs[j]}"] = {}
        for k, directory in enumerate(batch):
            print(directory)
            print(task_names[k])
            csv_path = directory / "merged_data.csv"

            cmd = f"python3 src/inspect_data.py -p {csv_path}"
            subprocess.check_output(cmd, shell=True)
            print(f"{csv_path} is inspected.")
            inspect_path = directory / "result.json"
            with open(inspect_path) as f:
                inspect_data = json.load(f)

            power = round(inspect_data["Power"], 2)
            powers[f"{cpu_freqs[i]}"][f"{tpu_freqs[j]}"][
                f"{task_names[k]}"
            ] = power

            # cmd = f"python3 src/visualize.py -p {csv_path}"
            # subprocess.check_output(cmd, shell=True)
            # print(f"{csv_path} is visualized.")
            # image_path = directory / "visualize.png"

            # copy(image_path, pf_directory / f"visualize_{i}_{j}_{k}.png")

    print()
print(powers)

# 첫 번째 그래프: TPU freq 500일 때의 task 별 CPU Frequency에 따른 bar plot
fig, ax = plt.subplots()
bar_width = 0.2
index = np.arange(len(task_names))

for i, cpu_freq in enumerate(cpu_freqs):
    power = [powers[f"{cpu_freq}"]["500"][task] for task in task_names]
    ax.bar(
        index + i * bar_width,
        power,
        bar_width,
        label=f"CPU {cpu_freq} GHz",
    )

ax.set_xlabel("Task")
ax.set_ylabel("Power (A)")
ax.set_title("Power Dissipation by Task and CPU Frequency (TPU Freq 500 MHz)")
ax.set_xticks(index + bar_width)
ax.set_xticklabels(task_names)
ax.legend()

plt.ylim(0, 6)
plt.tight_layout()
plt.savefig(pf_directory / f"Fig1.png")
plt.close()

# 두 번째 그래프: CPU freq를 1.5로 고정하고, TPU freq 4개를 하나의 포인트에 그리는 방식
fig, ax = plt.subplots()
bar_width = 0.15
index = np.arange(len(task_names))

for i, tpu_freq in enumerate(tpu_freqs):
    power = [powers["1.5"][f"{tpu_freq}"][task] for task in task_names]
    ax.bar(
        index + i * bar_width, power, bar_width, label=f"TPU {tpu_freq} GHz"
    )

ax.set_xlabel("Task")
ax.set_ylabel("Power (A)")
ax.set_title("Power Dissipation by Task and TPU Frequency (CPU Freq 1.5 GHz)")
ax.set_xticks(index + 1.5 * bar_width)
ax.set_xticklabels(task_names)
ax.legend()

plt.ylim(0, 6)
plt.tight_layout()
plt.savefig(pf_directory / f"Fig2.png")
plt.close()
