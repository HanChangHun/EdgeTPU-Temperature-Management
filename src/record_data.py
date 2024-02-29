import argparse
from pathlib import Path
import subprocess
import time
import asyncio
import aiohttp
import requests

import pandas as pd

ambient_url = "https://asia-northeast1-center-309-68aa8.cloudfunctions.net/getCenter309Temperature"
power_url1 = "https://asia-northeast1-center-309-68aa8.cloudfunctions.net/getUM34CPower1"
power_url2 = "https://asia-northeast1-center-309-68aa8.cloudfunctions.net/getUM34CPower2"

session = requests.Session()


async def fetch_data(session, url):
    async with session.get(url) as response:
        return await response.json()


async def fetch_web_data_async(duration, data_list, start_time, power_url):
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

            # Update next runtime
            next_run_time += 1

            print(
                f"web data collected at {time.time() - start_time:.2f} seconds since start"
            )


async def fetch_cdb_temperature_async(
    duration, port, username, host, result_path
):
    # Adjust this command as necessary
    cmd = f"./src/CDB_read_proc_temperature.sh -t {duration} -p {port} -u {username} -h {host}"
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE
    )
    stdout, _ = await process.communicate()
    result = stdout.decode().strip()
    result_path.append(result)


async def fetch_all_data(duration, port, username, host, power_url):
    web_data = []
    cdb_result_path = []
    start_time = time.time()

    # 비동기 작업 실행 및 데이터 수집
    web_task = asyncio.create_task(
        fetch_web_data_async(duration, web_data, start_time, power_url)
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
        "-u", dest="username", type=str, default="mendel", help="User name"
    )
    parser.add_argument("-H", dest="host", type=str, help="Host IP")
    parser.add_argument(
        "-p", dest="port", type=int, default=22, help="Port number"
    )
    parser.add_argument(
        "-t", dest="dur", type=int, default=10, help="Duration in seconds"
    )
    parser.add_argument(
        "-P",
        "--power_num",
        dest="power_num",
        type=int,
        default=1,
        help="Power URL number (1 or 2)",
    )

    args = parser.parse_args()
    duration = args.dur
    port = args.port
    username = args.username
    host = args.host
    power_num = args.power_num

    if power_num == 1:
        power_url = power_url1
    elif power_num == 2:
        power_url = power_url2
    else:
        raise ValueError("Invalid power URL number")

    loop = asyncio.get_event_loop()
    web_data, cdb_result_path = loop.run_until_complete(
        fetch_all_data(duration, port, username, host, power_url)
    )
    loop.close()

    # TODO: Change file path!!!
    timestamp_str = cdb_result_path[0]
    result_dir = Path(f"result/{timestamp_str}")

    web_df = pd.DataFrame(web_data, columns=["Power", "Ambient Temperature"])
    cdb_df = pd.read_csv(result_dir / "proc_temp_data.csv")
    merged_df = pd.concat([cdb_df, web_df], axis=1)
    print(merged_df.head())

    # Save merged data as CSV file
    merged_df.to_csv(result_dir / "merged_data.csv", index=False)


if __name__ == "__main__":
    main()
