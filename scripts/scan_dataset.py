from pathlib import Path
from collections import Counter, defaultdict
import re

import pandas as pd
import pyarrow.parquet as pq


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "player_data"

DAY_PATTERN = "February_*"


def decode_value(value):
    """Decode parquet byte values into normal strings."""
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def is_bot(user_id: str) -> bool:
    """
    According to the supplied README:
    - Human IDs are UUIDs
    - Bot IDs are numeric
    """
    return str(user_id).isdigit()


def load_parquet_file(file_path: Path) -> pd.DataFrame:
    table = pq.read_table(file_path)
    df = table.to_pandas()

    for column in ["user_id", "match_id", "map_id", "event"]:
        if column in df.columns:
            df[column] = df[column].apply(decode_value)

    return df


def main():
    print("=" * 80)
    print("LILA BLACK - FULL DATASET SCAN")
    print("=" * 80)

    day_folders = sorted(DATA_ROOT.glob(DAY_PATTERN))

    if not day_folders:
        raise FileNotFoundError(
            f"No folders matching {DAY_PATTERN} were found inside {DATA_ROOT}"
        )

    total_files = 0
    total_rows = 0
    successful_files = 0
    failed_files = 0

    files_per_day = Counter()
    rows_per_day = Counter()

    event_counts = Counter()
    map_counts = Counter()

    unique_users = set()
    unique_humans = set()
    unique_bots = set()
    unique_matches = set()

    match_maps = defaultdict(set)
    match_users = defaultdict(set)

    min_x = None
    max_x = None
    min_y = None
    max_y = None
    min_z = None
    max_z = None

    earliest_ts = None
    latest_ts = None

    failed_paths = []

    print("\nScanning folders...\n")

    for day_folder in day_folders:

        day_name = day_folder.name

        data_files = sorted(day_folder.glob("*.nakama-0"))

        print(f"{day_name}: {len(data_files)} files")

        files_per_day[day_name] = len(data_files)
        total_files += len(data_files)

        for index, file_path in enumerate(data_files, start=1):

            try:
                df = load_parquet_file(file_path)

                successful_files += 1
                total_rows += len(df)
                rows_per_day[day_name] += len(df)

                if df.empty:
                    continue

                required_columns = {
                    "user_id",
                    "match_id",
                    "map_id",
                    "x",
                    "y",
                    "z",
                    "ts",
                    "event",
                }

                missing_columns = required_columns - set(df.columns)

                if missing_columns:
                    raise ValueError(
                        f"Missing columns: {sorted(missing_columns)}"
                    )

                # ---------------------------------------------------------
                # USERS
                # ---------------------------------------------------------

                users = df["user_id"].dropna().astype(str).unique()

                for user_id in users:
                    unique_users.add(user_id)

                    if is_bot(user_id):
                        unique_bots.add(user_id)
                    else:
                        unique_humans.add(user_id)

                # ---------------------------------------------------------
                # MATCHES
                # ---------------------------------------------------------

                matches = df["match_id"].dropna().astype(str).unique()

                for match_id in matches:
                    unique_matches.add(match_id)

                # ---------------------------------------------------------
                # MAPS
                # ---------------------------------------------------------

                for map_id, count in df["map_id"].value_counts().items():
                    map_counts[str(map_id)] += int(count)

                # ---------------------------------------------------------
                # EVENTS
                # ---------------------------------------------------------

                for event, count in df["event"].value_counts().items():
                    event_counts[str(event)] += int(count)

                # ---------------------------------------------------------
                # MATCH -> MAP / USER RELATIONSHIPS
                # ---------------------------------------------------------

                for _, row in df[["match_id", "map_id", "user_id"]].drop_duplicates().iterrows():

                    match_id = str(row["match_id"])
                    map_id = str(row["map_id"])
                    user_id = str(row["user_id"])

                    match_maps[match_id].add(map_id)
                    match_users[match_id].add(user_id)

                # ---------------------------------------------------------
                # COORDINATES
                # ---------------------------------------------------------

                current_min_x = df["x"].min()
                current_max_x = df["x"].max()

                current_min_y = df["y"].min()
                current_max_y = df["y"].max()

                current_min_z = df["z"].min()
                current_max_z = df["z"].max()

                min_x = current_min_x if min_x is None else min(min_x, current_min_x)
                max_x = current_max_x if max_x is None else max(max_x, current_max_x)

                min_y = current_min_y if min_y is None else min(min_y, current_min_y)
                max_y = current_max_y if max_y is None else max(max_y, current_max_y)

                min_z = current_min_z if min_z is None else min(min_z, current_min_z)
                max_z = current_max_z if max_z is None else max(max_z, current_max_z)

                # ---------------------------------------------------------
                # TIMESTAMPS
                # ---------------------------------------------------------

                file_start = df["ts"].min()
                file_end = df["ts"].max()

                if pd.notna(file_start):
                    earliest_ts = (
                        file_start
                        if earliest_ts is None
                        else min(earliest_ts, file_start)
                    )

                if pd.notna(file_end):
                    latest_ts = (
                        file_end
                        if latest_ts is None
                        else max(latest_ts, file_end)
                    )

            except Exception as exc:

                failed_files += 1
                failed_paths.append((file_path, str(exc)))

                print(f"\nFAILED:")
                print(file_path)
                print(exc)

    # =====================================================================
    # VALIDATION
    # =====================================================================

    matches_with_multiple_maps = {
        match_id: maps
        for match_id, maps in match_maps.items()
        if len(maps) > 1
    }

    players_per_match = [
        len(users)
        for users in match_users.values()
    ]

    # =====================================================================
    # RESULTS
    # =====================================================================

    print("\n")
    print("=" * 80)
    print("SCAN RESULTS")
    print("=" * 80)

    print("\nFILES")
    print("-" * 40)
    print("Total files:      ", total_files)
    print("Successful files: ", successful_files)
    print("Failed files:     ", failed_files)

    print("\nROWS")
    print("-" * 40)
    print("Total rows:", total_rows)

    print("\nFILES PER DAY")
    print("-" * 40)

    for day, count in sorted(files_per_day.items()):
        print(f"{day:<15} {count:>6}")

    print("\nROWS PER DAY")
    print("-" * 40)

    for day, count in sorted(rows_per_day.items()):
        print(f"{day:<15} {count:>8}")

    print("\nPLAYERS")
    print("-" * 40)
    print("Unique users:  ", len(unique_users))
    print("Human players: ", len(unique_humans))
    print("Bot IDs:       ", len(unique_bots))

    print("\nMATCHES")
    print("-" * 40)
    print("Unique matches:", len(unique_matches))

    if players_per_match:
        print(
            "Players per match:",
            f"min={min(players_per_match)},",
            f"max={max(players_per_match)},",
            f"avg={sum(players_per_match) / len(players_per_match):.2f}",
        )

    print("\nMAP EVENT ROW COUNTS")
    print("-" * 40)

    for map_name, count in map_counts.most_common():
        print(f"{map_name:<20} {count:>8}")

    print("\nEVENT COUNTS")
    print("-" * 40)

    for event, count in event_counts.most_common():
        percentage = (count / total_rows * 100) if total_rows else 0

        print(
            f"{event:<20}"
            f"{count:>8}"
            f"   {percentage:>6.2f}%"
        )

    print("\nGLOBAL COORDINATE RANGE")
    print("-" * 40)

    print(f"X: {min_x} -> {max_x}")
    print(f"Y: {min_y} -> {max_y}")
    print(f"Z: {min_z} -> {max_z}")

    print("\nGLOBAL TIMESTAMP RANGE")
    print("-" * 40)

    print("Earliest:", earliest_ts)
    print("Latest:  ", latest_ts)

    print("\nDATA VALIDATION")
    print("-" * 40)

    print(
        "Matches associated with multiple maps:",
        len(matches_with_multiple_maps),
    )

    if matches_with_multiple_maps:

        for match_id, maps in list(
            matches_with_multiple_maps.items()
        )[:10]:

            print(match_id, maps)

    print("\nFAILED FILES")
    print("-" * 40)

    if failed_paths:
        for file_path, error in failed_paths:
            print(file_path)
            print("   Error:", error)
    else:
        print("None")

    print("\n")
    print("=" * 80)
    print("DATASET SCAN COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()