import argparse
from pathlib import Path
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


async def fetch_web_data_async(
    duration, data_list, start_time, power_url, interval=1
):
    async with aiohttp.ClientSession() as session:
        next_run_time = start_time
        total_iter = int(duration / interval)
        for _ in range(total_iter):
            while time.time() < next_run_time:
                await asyncio.sleep(1e-4)  # Wait a short time

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
            next_run_time += interval

            print(
                f"web data collected at {time.time() - start_time:.2f} seconds since start"
            )


async def fetch_cdb_temperature_async(
    username, host, port, duration, interval, result_path
):
    # Adjust this command as necessary
    cmd = f"./src/CDB_read_proc_temperature.sh -u {username} -H {host} -p {port} \
                                                -t {duration} -i {interval} -o {result_path}"
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE
    )
    stdout, _ = await process.communicate()
    print(stdout.decode().strip())


async def fetch_all_data(
    username, host, port, duration, power_url, interval, result_path
):
    web_data = []
    start_time = time.time()

    # 비동기 작업 실행 및 데이터 수집
    web_task = asyncio.create_task(
        fetch_web_data_async(
            duration, web_data, start_time, power_url, interval
        )
    )
    cdb_task = asyncio.create_task(
        fetch_cdb_temperature_async(
            username, host, port, duration, interval, result_path
        )
    )

    await asyncio.gather(web_task, cdb_task)

    return web_data


def main():
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "-u", "--user", type=str, default="mendel", help="User name"
    )
    parser.add_argument(
        "-H", "--host", type=str, help="Host IP", required=True
    )
    parser.add_argument(
        "-p", "--port", type=int, default=22, help="Port number"
    )
    parser.add_argument(
        "-t", "--dur", type=int, default=10, help="Duration in seconds"
    )
    parser.add_argument(
        "-P",
        "--power_num",
        type=int,
        default=1,
        help="Power URL number (1 or 2)",
    )
    parser.add_argument(
        "-i", "--interval", type=float, default=1, help="Duration in seconds"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="result", help="Output directory"
    )

    args = parser.parse_args()

    # Set up result directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    result_dir = output_dir

    # Select power URL with power_num
    if args.power_num == 1:
        power_url = power_url1
    elif args.power_num == 2:
        power_url = power_url2
    else:
        raise ValueError("Invalid power URL number")

    # Collect data
    loop = asyncio.get_event_loop()
    web_data = loop.run_until_complete(
        fetch_all_data(
            args.user,
            args.host,
            args.port,
            args.dur,
            power_url,
            args.interval,
            result_dir,
        )
    )
    loop.close()

    # Concatenate data
    web_df = pd.DataFrame(web_data, columns=["Power", "Ambient Temperature"])
    cdb_df = pd.read_csv(result_dir / "proc_temp_data.csv")
    merged_df = pd.concat([cdb_df, web_df], axis=1)
    print(merged_df.head())

    # Save merged data as CSV file
    merged_df.to_csv(result_dir / "merged_data.csv", index=False)


if __name__ == "__main__":
    main()
