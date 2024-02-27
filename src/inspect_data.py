import pandas as pd
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--csv_path",
        type=str,
        required=True,
        help="Path to CSV file to analyze",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    result_json_path = csv_path.parent / "result.json"

    data = pd.read_csv(csv_path)
    averages = data.mean()
    results = averages.to_dict()

    # Calculate Thermal Resistance
    R = (
        averages["CPU Temperature"] - averages["Ambient Temperature"]
    ) / averages["Power"]
    results["R"] = R

    with open(result_json_path, "w") as f:
        json.dump(results, f, indent=4)


if __name__ == "__main__":
    main()
