import argparse
import json
import csv
from pathlib import Path
import time
from pymongo import MongoClient


with open("mongodb_config.json", "r") as f:
    db_config = json.load(f)

client = MongoClient(db_config["client_url"])
db = client[db_config["db_name"]]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--db_config",
        type=str,
        default="mongodb_config.json",
        help="DB config file",
    )

    args = parser.parse_args()

    with open(args.db_config, "r") as f:
        db_config = json.load(f)

    client = MongoClient(db_config["client_url"])
    db = client[db_config["db_name"]]

    center_collection = db["Center309"]
    monsoon_collection = db["monsoon"]

    interval = 0.1
    last_upload_time = time.time()
    while True:
        if time.time() - last_upload_time < interval:
            time.sleep(1e-4)
            continue

        data = {}
        data["timestamp"] = time.time() * 1000  # in ms
        data["Ambient Temperature"] = center_collection.find_one(
            {"device_id": "center309_1"}
        )["t1"]
        data["Power"] = monsoon_collection.find_one(
            {"device_id": "monsoon_1"}
        )["power"]

        print(data)
        csv_file_path = "temp/sensor.csv"

        # CSV 파일이 존재하지 않으면 헤더를 포함하여 생성한다.
        with open(csv_file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["timestamp", "Ambient Temperature", "Power"]
            )  # 헤더 작성
            writer.writerow(
                [data["timestamp"], data["Ambient Temperature"], data["Power"]]
            )  # 최신 데이터 행 작성

        last_upload_time += interval
