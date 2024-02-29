import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
from pathlib import Path


def visualize_data(csv_path):
    df = pd.read_csv(csv_path)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="ms")
    result_dir = Path(csv_path).parent

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # 온도 데이터의 Y축 범위 설정
    temperature_cols = [
        "CPU Temperature",
        "TPU Temperature",
        "Ambient Temperature",
    ]
    temperature_range = [
        df[temperature_cols].min().min(),
        df[temperature_cols].max().max(),
    ]
    temperature_buffer = (temperature_range[1] - temperature_range[0]) * 0.1
    ax1.set_ylim([0, temperature_range[1] + temperature_buffer])

    color = "tab:red"
    ax1.set_xlabel("Timestamp")
    ax1.set_ylabel("Temperature (°C)", color=color)
    ax1.plot(
        df["Timestamp"],
        df["CPU Temperature"],
        label="CPU Temperature",
        color="red",
        marker="o",
    )
    ax1.plot(
        df["Timestamp"],
        df["TPU Temperature"],
        label="TPU Temperature",
        color="maroon",
        marker="x",
    )
    ax1.plot(
        df["Timestamp"],
        df["Ambient Temperature"],
        label="Ambient Temperature",
        color="salmon",
        marker="^",
    )
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.set_ylim([0, 80])  # Temperature의 Y축 범위 설정

    ax2 = ax1.twinx()  # 오른쪽 Y축 생성
    color = "tab:blue"
    ax2.set_ylabel("Power", color=color)  # 오른쪽 Y축 레이블
    ax2.plot(
        df["Timestamp"], df["Power"], label="Power", color="blue", marker="s"
    )
    ax2.tick_params(axis="y", labelcolor=color)
    ax2.set_ylim([0, 7.5])  # Power의 Y축 범위 설정

    tz = pytz.timezone("Asia/Seoul")
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax1.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y-%m-%d %H:%M:%S", tz=tz)
    )
    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")

    legend = fig.legend(loc="lower right", bbox_to_anchor=(0.93, 0.3))
    plt.tight_layout(pad=2.0)
    plt.title("Temperature and Power over Time")
    plt.grid(True)
    plt.savefig(result_dir / "visualize.png")


def main():
    parser = argparse.ArgumentParser(description="Data visualization.")
    parser.add_argument(
        "-p",
        "--csv_path",
        type=str,
        required=True,
        help="Path to CSV file to analyze",
    )

    args = parser.parse_args()
    csv_path = args.csv_path

    visualize_data(csv_path)


if __name__ == "__main__":
    main()
