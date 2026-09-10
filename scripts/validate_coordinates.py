from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "player_data"


MAP_CONFIG = {
    "AmbroseValley": {
        "scale": 900,
        "origin_x": -370,
        "origin_z": -473,
    },

    "GrandRift": {
        "scale": 581,
        "origin_x": -290,
        "origin_z": -290,
    },

    "Lockdown": {
        "scale": 1000,
        "origin_x": -500,
        "origin_z": -500,
    },
}


def decode_value(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")

    return value


def world_to_uv(x, z, config):

    u = (x - config["origin_x"]) / config["scale"]
    v = (z - config["origin_z"]) / config["scale"]

    return u, v


def main():

    print("=" * 80)
    print("LILA BLACK - COORDINATE VALIDATION")
    print("=" * 80)

    total_rows = 0
    valid_rows = 0
    outside_rows = 0

    per_map = {
        map_name: {
            "total": 0,
            "valid": 0,
            "outside": 0,
            "min_u": None,
            "max_u": None,
            "min_v": None,
            "max_v": None,
        }
        for map_name in MAP_CONFIG
    }

    outside_examples = []

    for day_folder in sorted(DATA_ROOT.glob("February_*")):

        print(f"\nChecking {day_folder.name}...")

        for file_path in sorted(day_folder.glob("*.nakama-0")):

            try:
                table = pq.read_table(
                    file_path,
                    columns=["map_id", "x", "z"]
                )

                df = table.to_pandas()

            except Exception as exc:

                print(
                    f"Could not read {file_path.name}: {exc}"
                )

                continue

            if df.empty:
                continue

            df["map_id"] = df["map_id"].apply(decode_value)

            for row in df.itertuples(index=False):

                map_name = str(row.map_id)

                if map_name not in MAP_CONFIG:
                    print(
                        f"WARNING: Unknown map '{map_name}'"
                    )

                    continue

                config = MAP_CONFIG[map_name]

                u, v = world_to_uv(
                    row.x,
                    row.z,
                    config,
                )

                stats = per_map[map_name]

                stats["total"] += 1
                total_rows += 1

                stats["min_u"] = (
                    u
                    if stats["min_u"] is None
                    else min(stats["min_u"], u)
                )

                stats["max_u"] = (
                    u
                    if stats["max_u"] is None
                    else max(stats["max_u"], u)
                )

                stats["min_v"] = (
                    v
                    if stats["min_v"] is None
                    else min(stats["min_v"], v)
                )

                stats["max_v"] = (
                    v
                    if stats["max_v"] is None
                    else max(stats["max_v"], v)
                )

                inside_map = (
                    0 <= u <= 1
                    and
                    0 <= v <= 1
                )

                if inside_map:

                    stats["valid"] += 1
                    valid_rows += 1

                else:

                    stats["outside"] += 1
                    outside_rows += 1

                    if len(outside_examples) < 20:

                        outside_examples.append(
                            {
                                "file": file_path.name,
                                "map": map_name,
                                "x": row.x,
                                "z": row.z,
                                "u": u,
                                "v": v,
                            }
                        )

    print("\n")
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)

    for map_name, stats in per_map.items():

        print(f"\n{map_name}")
        print("-" * 50)

        print("Rows:    ", stats["total"])
        print("Valid:   ", stats["valid"])
        print("Outside: ", stats["outside"])

        if stats["total"]:

            outside_percentage = (
                stats["outside"]
                / stats["total"]
                * 100
            )

            print(
                f"Outside %: {outside_percentage:.4f}%"
            )

        print(
            "U range:",
            stats["min_u"],
            "->",
            stats["max_u"],
        )

        print(
            "V range:",
            stats["min_v"],
            "->",
            stats["max_v"],
        )

    print("\nGLOBAL")
    print("-" * 50)

    print("Total rows:  ", total_rows)
    print("Valid rows:  ", valid_rows)
    print("Outside rows:", outside_rows)

    if total_rows:

        print(
            f"Outside percentage: "
            f"{outside_rows / total_rows * 100:.4f}%"
        )

    print("\nOUTSIDE EXAMPLES")
    print("-" * 50)

    if outside_examples:

        for item in outside_examples:

            print(
                f"{item['map']} | "
                f"x={item['x']:.2f} "
                f"z={item['z']:.2f} | "
                f"u={item['u']:.4f} "
                f"v={item['v']:.4f}"
            )

    else:

        print("No coordinates outside map bounds.")

    print("\n")
    print("=" * 80)
    print("COORDINATE VALIDATION COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()