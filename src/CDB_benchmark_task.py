from pathlib import Path
import time
import argparse

import numpy as np
import pandas as pd
from pycoral.utils.edgetpu import make_interpreter


def benchmark_model(model_path: str, num_inferences: int = 100) -> float:
    interpreter = make_interpreter(model_path)
    interpreter.allocate_tensors()
    interpreter.invoke()

    exec_times = []
    for _ in range(num_inferences):
        start_time = time.perf_counter_ns()
        interpreter.invoke()
        exec_time = (time.perf_counter_ns() - start_time) / (1_000_000)
        exec_times.append(exec_time)

    return exec_times


def main():
    parser = argparse.ArgumentParser(description="Data visualization.")
    parser.add_argument("-m", "--model_path", type=str, required=True)
    parser.add_argument("-n", "--num_inferences", type=int, default=100)
    parser.add_argument("-o", "--output_name", type=str, required=True)

    args = parser.parse_args()
    model_path = args.model_path
    output_name = args.output_name
    num_inferences = args.num_inferences

    output_path = Path("/tmp/result") / output_name

    exec_times = benchmark_model(model_path, num_inferences)

    df = pd.DataFrame({"Inference Time": exec_times})
    df.to_csv(output_path, index=False)


if __name__ == "__main__":
    main()
