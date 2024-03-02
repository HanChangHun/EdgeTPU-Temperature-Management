import argparse

from collections import defaultdict
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd


def benchmark_model(args, cpu_freq, tpu_freq):
    user = args.user
    host = args.host
    port = args.port
    model_path = args.model_path
    num_iter = args.num_iter

    output_name = args.output_name
    output_name = f"{output_name}_{tpu_freq}_{cpu_freq}.csv"

    cmd = f"./src/CDB_benchmark_task.sh -u {user} -H {host} -p {port} \
            -m {model_path} -o {output_name} -n {num_iter} -t {tpu_freq} -c {cpu_freq}"
    output = subprocess.check_output(cmd, shell=True)
    print(output.decode())

    return output_name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--user", type=str, default="mendel", help="User name"
    )
    parser.add_argument(
        "-H", "--host", type=str, required=True, help="Host IP"
    )
    parser.add_argument(
        "-p", "--port", type=int, required=True, help="Port number"
    )
    parser.add_argument("-m", "--model_path", type=str, required=True)
    parser.add_argument("-o", "--output_name", type=str, required=True)
    parser.add_argument("-n", "--num_iter", type=int, default=100)

    args = parser.parse_args()

    tpu_freqs = [500, 250, 125, 62.5]
    cpu_freqs = [1.5, 1.0, 0.5]

    subprocess.check_output(
        f"./src/CDB_disable_fan.sh -u {args.user} -h {args.host} -p {args.port}",
        shell=True,
    )

    benchmarks = defaultdict(lambda: defaultdict(dict))

    for tpu_freq in tpu_freqs:
        for cpu_freq in cpu_freqs:
            output_name = benchmark_model(args, cpu_freq, tpu_freq)
            output_path = Path("result/benchmark") / output_name
            df = pd.read_csv(output_path, index_col=False)
            wcet = np.percentile(df["Inference Time"], 95)
            avg = df["Inference Time"].mean()
            benchmarks[f"{tpu_freq}"][f"{cpu_freq}"] = {
                "WCET": wcet,
                "Average": avg,
            }

    with open(f"result/benchmark/{args.output_name}.json", "w") as f:
        json.dump(benchmarks, f, indent=4)

    subprocess.check_output(
        f"./src/CDB_enable_fan.sh -u {args.user} -h {args.host} -p {args.port}",
        shell=True,
    )
    subprocess.check_output(
        f"./src/CDB_change_frequency.sh -u {args.user} -h {args.host} -p {args.port}",
        shell=True,
    )


if __name__ == "__main__":
    main()
