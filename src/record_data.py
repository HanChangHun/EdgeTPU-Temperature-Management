import argparse
import json
from pathlib import Path
import time
import asyncio
import aiohttp

from pymongo import MongoClient
import pandas as pd

with open("mongodb_config.json", "r") as f:
    db_config = json.load(f)

client = MongoClient(db_config["client_url"])
db = client[db_config["db_name"]]


async def fetch_sensor_data(duration, start_time, power_id, interval=1):
    data_list = []
    loop = asyncio.get_running_loop()

    center_collection = db["Center309"]
    um_collection = db["UM34C"]

    next_run_time = start_time
    total_iter = int(duration / interval)
    for _ in range(total_iter):
        while time.time() < next_run_time:
            await asyncio.sleep(1e-4)  # Wait a short time

        power_response = await loop.run_in_executor(
            None, um_collection.find_one, {"device_id": power_id}
        )
        ambient_response = await loop.run_in_executor(
            None, center_collection.find_one, {"device_id": "center309_1"}
        )

        data_list.append([power_response["power"], ambient_response["t1"]])

        # Update next runtime
        next_run_time += interval
        print(
            f"Sensor data collected at {time.time() - start_time:.2f}"
            f" seconds since start. Data: {data_list[-1]}"
        )

    return data_list


async def fetch_cdb_temperature(
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
    username, host, port, duration, power_id, interval, result_path
):
    start_time = time.time()

    # 비동기 작업 실행 및 데이터 수집
    sensor_task = asyncio.create_task(
        fetch_sensor_data(duration, start_time, power_id, interval)
    )
    cdb_task = asyncio.create_task(
        fetch_cdb_temperature(
            username, host, port, duration, interval, result_path
        )
    )

    sensor_data, _ = await asyncio.gather(sensor_task, cdb_task)

    return sensor_data


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
        power_id = "um34c_1"
    elif args.power_num == 2:
        power_id = "um34c_2"
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
            power_id,
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
