import argparse
import subprocess
import threading


def execute_task(user, host, port, model_path, wcet, utilization, duration):
    cmd = f"./src/CDB_exec_task.sh -u {user} -H {host} -p {port} \
            -m {model_path} -e {wcet} -U {utilization} -t {duration}"
    output = subprocess.check_output(cmd, shell=True)
    print(output.decode().strip())


def record_data(user, host, port, duration, power_url, interval, result_path):
    cmd = f"python3 src/record_data.py -u {user} -H {host} \
            -p {port} -t {duration} -P {power_url} \
            -i {interval} -o {result_path}"
    output = subprocess.check_output(cmd, shell=True)
    print(output.decode().strip())


def main():
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "-u", dest="user", type=str, default="mendel", help="User name"
    )
    parser.add_argument("-H", dest="host", type=str, help="Host IP")
    parser.add_argument(
        "-p", dest="port", type=int, default=22, help="Port number"
    )

    parser.add_argument(
        "-P",
        "--power_num",
        dest="power_num",
        type=int,
        default=1,
        help="Power URL number (1 or 2)",
    )
    parser.add_argument("-t", "--duration", type=int, required=True)
    parser.add_argument("-i", "--interval", type=float, default=0.25)
    parser.add_argument("-o", "--output", type=str, required=True)

    parser.add_argument("-m", "--model_path", type=str, required=True)
    parser.add_argument("-e", "--wcet", type=float, required=True)
    parser.add_argument("-U", "--utilization", type=float, required=True)

    args = parser.parse_args()

    exec_thread = threading.Thread(
        target=execute_task,
        args=(
            args.user,
            args.host,
            args.port,
            args.model_path,
            args.wcet,
            args.utilization,
            args.duration,
        ),
    )
    record_thread = threading.Thread(
        target=record_data,
        args=(
            args.user,
            args.host,
            args.port,
            args.duration,
            args.power_num,
            args.interval,
            args.output,
        ),
    )

    subprocess.check_output(
        f"./src/CDB_disable_fan.sh -u {args.user} -H {args.host} -p {args.port}",
        shell=True,
    )

    exec_thread.start()
    record_thread.start()

    exec_thread.join()
    record_thread.join()

    subprocess.check_output(
        f"./src/CDB_enable_fan.sh -u {args.user} -H {args.host} -p {args.port}",
        shell=True,
    )
    subprocess.check_output(
        f"./src/CDB_change_frequency.sh -u {args.user} -H {args.host} -p {args.port}",
        shell=True,
    )


if __name__ == "__main__":
    main()
