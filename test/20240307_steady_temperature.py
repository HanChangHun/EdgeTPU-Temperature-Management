import argparse
import time
import csv
import json
import threading
import subprocess
from pathlib import Path
from datetime import datetime

from tqdm import tqdm
from pymongo import MongoClient


with open("mongodb_config.json", "r") as f:
    db_config = json.load(f)

client = MongoClient(db_config["client_url"])
db = client[db_config["db_name"]]

center_collection = db["Center309"]
monsoon_collection = db["monsoon"]

model_paths = [
    "test_data/mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite",
    "test_data/efficientnet-edgetpu-L_quant_edgetpu.tflite",
    "test_data/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite",
]
model_names = ["mobilenet_v2", "efficientnet_l", "ssd_mobilenet_v2"]
utils = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]

freqs = [500, 250, 125, 62.5]
wcets_500 = [3.8, 25.98, 12.75]  # 500MHz
wcets_250 = [5.38, 36.24, 16.27]  # 250MHz
wcets_125 = [8.47, 58.34, 23.55]  # 125MHz
wcets_62_5 = [14.95, 105.2, 37.98]  # 62.5MHz
wcets_list = [wcets_500, wcets_250, wcets_125, wcets_62_5]


def record_sensor_data(result_path, stop_event):
    # read sensor data with 0.1 second interval and write csv file
    interval = 0.1

    last_temp = 0
    last_power = 0
    last_record_time = time.time()
    while not stop_event.is_set():
        if time.time() - last_record_time < interval:
            time.sleep(1e-4)
            continue

        try:
            current_time = int(time.time() * 1000)  # in ms
            center_data = center_collection.find_one(
                {"device_id": "center309_1"}
            )
            monsoon_data = monsoon_collection.find_one(
                {"device_id": "monsoon_1"}
            )

            temp = (
                center_data["t1"]
                if center_data and center_data.get("t1") is not None
                else last_temp
            )
            power = (
                monsoon_data["power"]
                if monsoon_data and monsoon_data.get("power") is not None
                else last_power
            )

            last_temp = temp
            last_power = power

            # write csv
            if not Path(result_path).exists():
                with open(result_path, "w", newline="") as f:
                    f.write("timestamp,Ambient Temperature,Power\n")

            with open(result_path, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([current_time, temp, power])

            last_record_time += interval

        except Exception as e:
            continue


def execute_task(user, host, port, model_path, wcet, utilization, duration):
    cmd = f"./src/CDB_exec_task.sh -u {user} -H {host} -p {port} \
            -m {model_path} -e {wcet} -U {utilization} -t {duration}"
    output = subprocess.check_output(cmd, shell=True)
    print(output.decode().strip())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-u", "--user", type=str, default="mendel", help="User name"
    )
    parser.add_argument(
        "-H", "--host", type=str, help="Host IP", required=True
    )
    parser.add_argument(
        "-p", "--port", type=int, default=22, help="Port number"
    )

    args = parser.parse_args()

    result_name = "20240328"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = Path("result") / f"{result_name}/{timestamp}"

    interval = 0.1
    stop_event = threading.Event()

    # Calculate the total number of experiments
    total_experiments = len(freqs) * len(model_names) * len(utils)

    # Create a progress bar using tqdm

    progress_bar = tqdm(
        total=total_experiments,
        unit="experiment",
        desc="Progress",
        position=0,
        leave=True,
        dynamic_ncols=True,
    )

    # Start the experiment
    for freq, wcets in zip(freqs, wcets_list):
        # Set frequency
        cmd = f"src/CDB_change_frequency.sh -u {args.user} -H {args.host} -p {args.port} -t {freq} "
        subprocess.run(cmd, shell=True)

        for model in model_names:
            model_idx = model_names.index(model)
            model_path = model_paths[model_idx]
            wcet = wcets[model_idx]

            for util in utils:
                tqdm.write(
                    f"Start {model} with {util} utilization at {freq}MHz"
                )

                # Stage 1: Cool Down
                # Set Duration
                duration = 180

                # turn on the fan
                cmd = f"src/CDB_enable_fan.sh -u {args.user} -H {args.host} -p {args.port}"
                subprocess.run(cmd, shell=True)

                # Record Data
                # ambient temperature & power
                sensor_data_dir = result_path / f"{model}/{freq}/{util}/s1"
                sensor_data_dir.mkdir(parents=True, exist_ok=True)
                sensor_data_path = sensor_data_dir / "sensor_data.csv"
                sensor_thread_1 = threading.Thread(
                    target=record_sensor_data,
                    args=(sensor_data_path, stop_event),
                )
                sensor_thread_1.start()

                # processor temperature
                s1_result_path = result_path / f"{model}/{freq}/{util}/s1"
                cmd = f"./src/CDB_read_proc_temperature.sh -u {args.user} -H {args.host} -p {args.port} \
                                                -t {duration} -i {interval} -o {s1_result_path}"
                subprocess.run(cmd, shell=True)

                stop_event.set()
                sensor_thread_1.join()
                stop_event.clear()

                # Stage 2: Idle
                # Set Duration
                duration = 300

                # turn off the fan
                cmd = f"src/CDB_disable_fan.sh -u {args.user} -H {args.host} -p {args.port}"
                subprocess.run(cmd, shell=True)

                # Record Data
                # ambient temperature & power
                sensor_data_dir = result_path / f"{model}/{freq}/{util}/s2"
                sensor_data_dir.mkdir(parents=True, exist_ok=True)
                sensor_data_path = sensor_data_dir / "sensor_data.csv"
                sensor_thread_2 = threading.Thread(
                    target=record_sensor_data,
                    args=(sensor_data_path, stop_event),
                )
                sensor_thread_2.start()

                # processor temperature
                s2_result_path = result_path / f"{model}/{freq}/{util}/s2"
                cmd = f"./src/CDB_read_proc_temperature.sh -u {args.user} -H {args.host} -p {args.port} \
                                                -t {duration} -i {interval} -o {s2_result_path}"
                subprocess.run(cmd, shell=True)

                stop_event.set()
                sensor_thread_2.join()
                stop_event.clear()

                # Stage 3: Run Inference
                # Set Duration
                duration = 3600

                # Record Data
                # ambient temperature & power
                sensor_data_dir = result_path / f"{model}/{freq}/{util}/s3"
                sensor_data_dir.mkdir(parents=True, exist_ok=True)
                sensor_data_path = sensor_data_dir / "sensor_data.csv"
                sensor_thread_3 = threading.Thread(
                    target=record_sensor_data,
                    args=(sensor_data_path, stop_event),
                )
                sensor_thread_3.start()

                # execute task
                # stop process that using libedgetpu.so
                tqdm.write("Stop process that using libedgetpu.so")
                cmd = f"ssh -p {args.port} {args.user}@{args.host} fuser -k -9 /usr/lib/aarch64-linux-gnu/libedgetpu.so.1"
                subprocess.run(cmd, shell=True)

                tqdm.write(
                    f"Start task {model} with {util} utilization at {freq}MHz"
                )
                exec_thread = threading.Thread(
                    target=execute_task,
                    args=(
                        args.user,
                        args.host,
                        args.port,
                        model_path,
                        wcet,
                        util,
                        duration,
                    ),
                )
                exec_thread.start()

                # processor temperature
                s3_result_path = result_path / f"{model}/{freq}/{util}/s3"
                cmd = f"./src/CDB_read_proc_temperature.sh -u {args.user} -H {args.host} -p {args.port} \
                                                -t {duration} -i {interval} -o {s3_result_path}"

                # it runs blocking
                subprocess.run(cmd, shell=True)

                stop_event.set()
                sensor_thread_3.join()
                exec_thread.join()

                stop_event.clear()

                # Update the progress bar
                progress_bar.update(1)

    # turn on the fan lastly
    cmd = f"src/CDB_enable_fan.sh -u {args.user} -H {args.host} -p {args.port}"
    subprocess.run(cmd, shell=True)

    # Set default frequency
    cmd = f"src/CDB_change_frequency.sh -u {args.user} -H {args.host} -p {args.port} "
    subprocess.run(cmd, shell=True)

    # Close the progress bar
    progress_bar.close()
