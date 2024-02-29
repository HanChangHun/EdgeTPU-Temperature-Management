import argparse
import time
from pycoral.utils.edgetpu import make_interpreter


def execute_task(model_path, period, duration):
    interpreter = make_interpreter(model_path)
    interpreter.allocate_tensors()

    start_time = time.perf_counter()
    next_run_time = start_time
    while True:
        if time.perf_counter() > start_time + duration:
            break
        if time.perf_counter() < next_run_time:
            time.sleep(1e-4)
            continue

        # print(
        #     f"Task executed at {time.perf_counter() - start_time:.2f} seconds since start"
        # )
        interpreter.invoke()
        next_run_time += period


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model_path", type=str, required=True)
    parser.add_argument("-e", "--wcet", type=float, required=True)
    parser.add_argument("-U", "--utilization", type=float, required=True)
    parser.add_argument("-t", "--duration", type=float, required=True)

    args = parser.parse_args()
    period = (args.wcet / args.utilization) / 1000  # in ms

    print(f"Task's WCET is {args.wcet} and utilization is {args.utilization}.")
    print(
        f"Execute task with period {period * 1000}ms and duration {args.duration}s"
    )

    execute_task(args.model_path, period, args.duration)


if __name__ == "__main__":
    main()
