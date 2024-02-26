import argparse
import time
import asyncio
import aiohttp
import requests

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz

power_url = "https://getum34cpower-4dpuk4m42q-uc.a.run.app/"
ambient_url = "https://getcenter309temperature-4dpuk4m42q-uc.a.run.app/"

session = requests.Session()


async def fetch_data(session, url):
    async with session.get(url) as response:
        return await response.json()


async def fetch_web_data_async(duration, data_list, start_time):
    async with aiohttp.ClientSession() as session:
        next_run_time = start_time
        for _ in range(duration):
            while time.time() < next_run_time:
                await asyncio.sleep(1e-4)  # 짧은 시간 대기 후 다시 확인

            power_task = asyncio.create_task(fetch_data(session, power_url))
            ambient_task = asyncio.create_task(
                fetch_data(session, ambient_url)
            )

            power_response = await power_task
            ambient_response = await ambient_task

            power = power_response["power"]
            ambient = ambient_response["t1"]

            data_list.append([power, ambient])

            # 다음 실행 시간 업데이트
            next_run_time += 1

            print(
                f"web data collected at {time.time() - start_time:.2f} seconds since start"
            )


async def fetch_cdb_temperature_async(
    duration, port, username, host, result_path
):
    # Adjust this command as necessary
    cmd = f"./read_proc_temperature_CDB.sh -t {duration} -p {port} -u {username} -h {host}"
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    result = stdout.decode().strip()
    result_path.append(result)


async def fetch_all_data(duration, port, username, host):
    web_data = []
    cdb_result_path = []
    start_time = time.time()

    # 비동기 작업 실행 및 데이터 수집
    web_task = asyncio.create_task(
        fetch_web_data_async(duration, web_data, start_time)
    )
    cdb_task = asyncio.create_task(
        fetch_cdb_temperature_async(
            duration, port, username, host, cdb_result_path
        )
    )

    await asyncio.gather(web_task, cdb_task)

    return web_data, cdb_result_path


def main():
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "-t", dest="dur", type=int, default=10, help="Duration in seconds"
    )
    parser.add_argument(
        "-p", dest="port", type=int, default=22, help="Port number"
    )
    parser.add_argument("-u", dest="username", type=str, help="User name")
    parser.add_argument("-H", dest="host", type=str, help="Host IP")

    args = parser.parse_args()
    duration = args.dur
    port = args.port
    username = args.username
    host = args.host

    ###################################
    # 데이터 추출
    ###################################
    loop = asyncio.get_event_loop()
    web_data, cdb_result_path = loop.run_until_complete(
        fetch_all_data(duration, port, username, host)
    )
    loop.close()

    date_str = cdb_result_path[0].split("_")[-2]
    time_str = cdb_result_path[0].split("_")[-1].split(".")[0]
    timestamp_str = date_str + "_" + time_str

    web_df = pd.DataFrame(web_data, columns=["Power", "Ambient Temperature"])
    cdb_df = pd.read_csv(cdb_result_path[0])
    merged_df = pd.concat([cdb_df, web_df], axis=1)
    print(merged_df.head())

    # 병합된 데이터를 CSV 파일로 저장
    merged_df.to_csv(f"result/merged_data_{timestamp_str}.csv", index=False)

    ###################################
    # 그래프 그리기
    ###################################
    merged_df["Timestamp"] = pd.to_datetime(merged_df["Timestamp"], unit="ms")
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # 온도 데이터의 Y축 범위 설정
    temperature_cols = [
        "CPU Temperature",
        "TPU Temperature",
        "Ambient Temperature",
    ]
    temperature_range = [
        merged_df[temperature_cols].min().min(),
        merged_df[temperature_cols].max().max(),
    ]
    temperature_buffer = (temperature_range[1] - temperature_range[0]) * 0.1
    ax1.set_ylim([0, temperature_range[1] + temperature_buffer])

    color = "tab:red"
    ax1.set_xlabel("Timestamp")
    ax1.set_ylabel("Temperature (°C)", color=color)
    ax1.plot(
        merged_df["Timestamp"],
        merged_df["CPU Temperature"],
        label="CPU Temperature",
        color="red",
        marker="o",
    )
    ax1.plot(
        merged_df["Timestamp"],
        merged_df["TPU Temperature"],
        label="TPU Temperature",
        color="maroon",
        marker="x",
    )
    ax1.plot(
        merged_df["Timestamp"],
        merged_df["Ambient Temperature"],
        label="Ambient Temperature",
        color="salmon",
        marker="^",
    )
    ax1.tick_params(axis="y", labelcolor=color)

    ax2 = ax1.twinx()  # 오른쪽 Y축 생성
    color = "tab:blue"
    ax2.set_ylabel("Power", color=color)  # 오른쪽 Y축 레이블
    ax2.plot(
        merged_df["Timestamp"],
        merged_df["Power"],
        label="Power",
        color="blue",
        marker="s",
    )
    ax2.tick_params(axis="y", labelcolor=color)
    ax2.set_ylim([0, 5])  # Power의 Y축 범위 설정

    tz = pytz.timezone("Asia/Seoul")
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax1.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y-%m-%d %H:%M:%S", tz=tz)
    )
    plt.setp(ax1.get_xticklabels(), ha="center", rotation=45)

    legend = fig.legend(loc="lower right", bbox_to_anchor=(0.95, 0.25))
    plt.tight_layout()
    plt.title("Temperature and Power over Time")
    plt.grid(True)
    plt.savefig(
        f"result/idle_vis_{timestamp_str}.png", bbox_extra_artists=(legend,)
    )


if __name__ == "__main__":
    main()
