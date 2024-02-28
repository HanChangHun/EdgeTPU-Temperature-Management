import argparse
import subprocess
import time


def benchmark_model(args, cpu_freq, tpu_freq):
    user = args.user
    host = args.host
    port = args.port
    model_path = args.model_path
    num_iter = args.num_iter

    output_name = args.output_name
    output_name = f"{output_name}_{cpu_freq}_{tpu_freq}.csv"

    cmd = f"./src/CDB_benchmark_task.sh -u {user} -h {host} -p {port} \
            -m {model_path} -o {output_name} -n {num_iter} -c {cpu_freq} -t {tpu_freq}"
    output = subprocess.check_output(cmd, shell=True)
    print(output.decode())


def main():
    parser = argparse.ArgumentParser(description="Process some integers.")
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

    cpu_freqs = [1.5, 1.0, 0.5]
    tpu_freqs = [500, 250, 125, 62.5]

    for tpu_freq in tpu_freqs:
        for cpu_freq in cpu_freqs:
            benchmark_model(args, cpu_freq, tpu_freq)


if __name__ == "__main__":
    main()
