from pathlib import Path
import subprocess
import matplotlib.pyplot as plt
import pandas as pd


def round_timestamp(ts):
    return (ts // 100) * 100


def visualize_two_csv(csv1, csv2, result_filename):
    df_csv1 = pd.read_csv(csv1)
    df_csv2 = pd.read_csv(csv2)

    # 100ms 단위로 Timestamp 반올림
    df_csv1["Timestamp"] = round_timestamp(df_csv1["Timestamp"])
    df_csv2["Timestamp"] = round_timestamp(df_csv2["Timestamp"])

    # 둘 중 늦게 시작한 시간 기준으로 설정
    start_time = max(df_csv1["Timestamp"].min(), df_csv2["Timestamp"].min())

    # 시작 시간 이후의 데이터만 필터링
    df_csv1 = df_csv1[df_csv1["Timestamp"] >= start_time]
    df_csv2 = df_csv2[df_csv2["Timestamp"] >= start_time]

    # 두 데이터프레임을 Timestamp를 기준으로 합치기
    df_merged = pd.merge_asof(
        df_csv1.sort_values("Timestamp"),
        df_csv2.sort_values("Timestamp"),
        on="Timestamp",
        direction="nearest",
    )

    df_merged["Timestamp"] = pd.to_datetime(df_merged["Timestamp"], unit="ms")
    df_merged.to_csv(f"{result_filename}.csv", index=False)
    print(df_merged.head())

    timestamp_min = df_merged["Timestamp"].min()
    timestamp_max = df_merged["Timestamp"].max()
    timestamp_middle = timestamp_min + (timestamp_max - timestamp_min) / 2

    # 그래프 그리기 시작
    fig, ax1 = plt.subplots()

    # 왼쪽 Y축 설정 (온도)
    color = "tab:red"
    ax1.set_xlabel("Timestamp")

    ax1.set_ylabel("Temperature (°C)", color=color)
    ax1.plot(
        df_merged["Timestamp"],
        df_merged["TPU Temperature"],
        label="TPU Temperature",
        color="orange",
    )

    ax1.plot(
        df_merged["Timestamp"],
        df_merged["Ambient Temperature"],
        label="Ambient Temperature",
        color="coral",
    )

    # Ambient Temperature의 최대, 최소 및 평균 계산
    max_ambient_temp = round(df_merged["Ambient Temperature"].max(), 2)
    min_ambient_temp = round(df_merged["Ambient Temperature"].min(), 2)
    avg_ambient_temp = round(df_merged["Ambient Temperature"].mean(), 2)

    # 최소, 최대, 평균 온도 텍스트 추가
    text_str = f"Min: {min_ambient_temp}°C, Max: {max_ambient_temp}°C, Avg: {avg_ambient_temp}°C"
    ax1.text(
        timestamp_middle,
        min_ambient_temp - 2,
        text_str,
        color="coral",
        ha="center",
        va="top",
        fontweight="bold",
    )

    ax1.tick_params(axis="y", labelcolor=color)
    ax1.legend(loc="upper left")
    ax1.set_ylim(15, 90)

    # TPU Temperature의 최고 온도 표시
    max_tpu_temp = df_merged["TPU Temperature"].max()
    ax1.axhline(y=max_tpu_temp, color="grey", linestyle="--")
    ax1.text(
        df_merged["Timestamp"].mean(),
        max_tpu_temp + 2,
        f"Max TPU Temp: {max_tpu_temp}°C",
        color="grey",
        fontweight="bold",
        ha="center",
        va="center",
    )

    # 오른쪽 Y축 설정 (전력)
    ax2 = ax1.twinx()
    color = "tab:blue"
    ax2.set_ylabel("Power (W)", color=color)
    ax2.plot(
        df_merged["Timestamp"],
        df_merged["Power"],
        label="Power",
        color="blue",
        alpha=0.2,
    )

    # Power 데이터의 이동 평균 계산
    window_size = 20  # 이동 평균 윈도우 크기를 조정하여 스무딩 정도 변경 가능
    rolling_power = df_merged["Power"].rolling(window=window_size).mean()
    ax2.plot(
        df_merged["Timestamp"],
        rolling_power,
        label="Power (Smoothed)",
        color="darkblue",
        linewidth=2,
    )

    # Power 데이터의 전체 평균 표시 (점선과 텍스트)
    average_power = df_merged["Power"].mean()
    ax2.axhline(
        y=average_power,
        color="green",
        linestyle="--",
    )
    ax2.text(
        df_merged["Timestamp"].mean(),
        average_power + 1,
        f"Avg Power: {average_power:.2f}W",
        color="green",
        fontweight="bold",
        ha="center",
        va="center",
    )

    ax2.tick_params(axis="y", labelcolor=color)
    ax2.legend(loc="upper right")
    ax2.set_ylim(0, 20)

    # 타이틀 및 레이아웃 설정
    plt.title("Temperature and Power Over Time")
    fig.tight_layout()

    plt.savefig(f"{result_filename}.png")
    subprocess.run(
        [
            "scp",
            "-P 20099",
            f"{result_filename}.png",
            "Changhun@210.107.198.220:/C/Users/Changhun/Downloads/temp",
        ]
    )


if __name__ == "__main__":
    base_dir = Path("result/20240307_steady_temperature")

    mobilenet_v2_dirs = []
    efficientnet_l_dirs = []
    ssd_mobilenet_v2_dirs = []

    model_names = ["mobilenet_v2", "efficientnet_l", "ssd_mobilenet_v2"]

    for path in base_dir.glob("*"):
        dirname = path.name
        if "ssd_mobilenet_v2" in dirname:
            ssd_mobilenet_v2_dirs.append(dirname)
        elif "mobilenet_v2" in dirname:
            mobilenet_v2_dirs.append(dirname)
        elif "efficientnet_l" in dirname:
            efficientnet_l_dirs.append(dirname)

    # 정렬 함수: 디렉토리 이름의 마지막 부분(부동소수점 숫자)을 추출하여 정렬 기준으로 사용
    def sort_key(dir_name):
        return float(dir_name.split("_")[-1])

    # 각 리스트를 부동소수점 숫자 기준으로 내림차순 정렬
    mobilenet_v2_dirs.sort(key=sort_key, reverse=True)
    efficientnet_l_dirs.sort(key=sort_key, reverse=True)
    ssd_mobilenet_v2_dirs.sort(key=sort_key, reverse=True)

    # 결과 출력 (실제 코드에는 포함하지 않음)
    print("mobilenet_v2_dirs:", mobilenet_v2_dirs)
    print("efficientnet_l_dirs:", efficientnet_l_dirs)
    print("ssd_mobilenet_v2_dirs:", ssd_mobilenet_v2_dirs)

    model_result_dirs = [
        mobilenet_v2_dirs,
        efficientnet_l_dirs,
        ssd_mobilenet_v2_dirs,
    ]

    for model_result_dir in model_result_dirs:
        for model_dir in model_result_dir:
            for stage in ["s1", "s2", "s3"]:
                csv1 = base_dir / model_dir / stage / "sensor_data.csv"
                csv2 = base_dir / model_dir / stage / "proc_temp_data.csv"
                result_filename = base_dir / model_dir / stage / "result"
                visualize_two_csv(csv1, csv2, result_filename)
