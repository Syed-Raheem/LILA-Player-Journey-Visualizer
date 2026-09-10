from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "player_data"


def find_first_data_file() -> Path:
    day_folders = sorted(DATA_ROOT.glob("February_*"))

    for day_folder in day_folders:
        for file_path in sorted(day_folder.iterdir()):
            if file_path.is_file() and file_path.name.endswith(".nakama-0"):
                return file_path

    raise FileNotFoundError("No .nakama-0 data files were found.")


def main():
    file_path = find_first_data_file()

    print("=" * 70)
    print("LILA BLACK - DATA INSPECTION")
    print("=" * 70)

    print("\nReading file:")
    print(file_path)

    table = pq.read_table(file_path)
    df = table.to_pandas()

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nShape:")
    print(df.shape)

    print("\nData types:")
    print(df.dtypes)

    print("\nFirst 10 rows:")
    print(df.head(10).to_string())

    print("\nRaw unique events:")
    print(df["event"].unique())

    df["event"] = df["event"].apply(
        lambda value: value.decode("utf-8")
        if isinstance(value, bytes)
        else value
    )

    print("\nDecoded unique events:")
    print(df["event"].unique())

    print("\nUser ID:")
    print(df["user_id"].iloc[0])

    print("\nMatch ID:")
    print(df["match_id"].iloc[0])

    print("\nMap:")
    print(df["map_id"].iloc[0])

    print("\nTimestamp range:")
    print("Start:", df["ts"].min())
    print("End:  ", df["ts"].max())

    print("\nCoordinate ranges:")
    print("X:", df["x"].min(), "->", df["x"].max())
    print("Y:", df["y"].min(), "->", df["y"].max())
    print("Z:", df["z"].min(), "->", df["z"].max())

    print("\nEvent counts:")
    print(df["event"].value_counts())

    print("\nInspection completed successfully.")


if __name__ == "__main__":
    main()