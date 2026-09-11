from pathlib import Path
from collections import defaultdict
import json

import pandas as pd
import pyarrow.parquet as pq

from config import MAP_CONFIG, MINIMAP_SIZE


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "player_data"

OUTPUT_ROOT = PROJECT_ROOT / "processed_data"
MATCH_OUTPUT_ROOT = OUTPUT_ROOT / "matches"


MOVEMENT_EVENTS = {
    "Position",
    "BotPosition",
}


EVENT_MARKER_TYPES = {
    "Kill",
    "Killed",
    "BotKill",
    "BotKilled",
    "KilledByStorm",
    "Loot",
}


def decode_value(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")

    return value


def clean_match_id(match_id: str) -> str:
    """
    match_id values contain '.nakama-0'.
    Keep the original ID for display, but remove the suffix
    when creating JSON filenames.
    """
    return str(match_id).replace(".nakama-0", "")


def is_bot(user_id: str) -> bool:
    return str(user_id).isdigit()


def world_to_minimap(x: float, z: float, map_id: str):
    config = MAP_CONFIG[map_id]

    u = (x - config["origin_x"]) / config["scale"]
    v = (z - config["origin_z"]) / config["scale"]

    pixel_x = u * MINIMAP_SIZE
    pixel_y = (1 - v) * MINIMAP_SIZE

    return {
        "u": round(float(u), 6),
        "v": round(float(v), 6),
        "px": round(float(pixel_x), 2),
        "py": round(float(pixel_y), 2),
    }


def load_all_files():
    """
    Read every parquet telemetry file and group them by match.
    """

    matches = defaultdict(list)

    print("=" * 80)
    print("LILA BLACK - PREPROCESSING")
    print("=" * 80)

    for day_folder in sorted(DATA_ROOT.glob("February_*")):

        day_name = day_folder.name

        print(f"\nLoading {day_name}...")

        files = sorted(day_folder.glob("*.nakama-0"))

        for file_index, file_path in enumerate(files, start=1):

            table = pq.read_table(file_path)
            df = table.to_pandas()

            for column in [
                "user_id",
                "match_id",
                "map_id",
                "event",
            ]:
                df[column] = df[column].apply(decode_value)

            if df.empty:
                continue

            match_id = str(df["match_id"].iloc[0])

            matches[match_id].append(
                {
                    "day": day_name,
                    "file": file_path,
                    "data": df,
                }
            )

    return matches


def build_match(match_id, player_files):

    frames = []

    day_names = set()

    for item in player_files:

        day_names.add(item["day"])

        frames.append(item["data"])

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    combined = combined.sort_values(
        "ts"
    ).reset_index(drop=True)

    map_ids = combined["map_id"].dropna().unique()

    if len(map_ids) != 1:
        raise ValueError(
            f"Match {match_id} has unexpected maps: {map_ids}"
        )

    map_id = str(map_ids[0])

    if map_id not in MAP_CONFIG:
        raise ValueError(
            f"Unknown map: {map_id}"
        )

    # ---------------------------------------------------------
    # MATCH TIME
    # ---------------------------------------------------------

    match_start = combined["ts"].min()
    match_end = combined["ts"].max()

    combined["elapsed_ms"] = (
        combined["ts"] - match_start
    ).dt.total_seconds() * 1000

    match_duration_ms = int(
        (
            match_end - match_start
        ).total_seconds()
        * 1000
    )

    # ---------------------------------------------------------
    # PLAYERS
    # ---------------------------------------------------------

    players = []

    grouped_players = combined.groupby(
        "user_id",
        sort=False,
    )

    for user_id, player_df in grouped_players:

        user_id = str(user_id)

        bot = is_bot(user_id)

        player_df = player_df.sort_values(
            "ts"
        )

        movement_rows = player_df[
            player_df["event"].isin(
                MOVEMENT_EVENTS
            )
        ]

        path = []

        for row in movement_rows.itertuples():

            pos = world_to_minimap(
                row.x,
                row.z,
                map_id,
            )

            path.append(
                {
                    "t": int(row.elapsed_ms),
                    "x": round(float(row.x), 2),
                    "y": round(float(row.y), 2),
                    "z": round(float(row.z), 2),
                    "u": pos["u"],
                    "v": pos["v"],
                    "px": pos["px"],
                    "py": pos["py"],
                }
            )

        # -----------------------------------------------------
        # PLAYER EVENTS
        # -----------------------------------------------------

        events = []

        event_rows = player_df[
            player_df["event"].isin(
                EVENT_MARKER_TYPES
            )
        ]

        for row in event_rows.itertuples():

            pos = world_to_minimap(
                row.x,
                row.z,
                map_id,
            )

            events.append(
                {
                    "type": str(row.event),
                    "t": int(row.elapsed_ms),
                    "x": round(float(row.x), 2),
                    "y": round(float(row.y), 2),
                    "z": round(float(row.z), 2),
                    "u": pos["u"],
                    "v": pos["v"],
                    "px": pos["px"],
                    "py": pos["py"],
                }
            )

        # -----------------------------------------------------
        # COUNTS
        # -----------------------------------------------------

        counts = (
            player_df["event"]
            .value_counts()
            .to_dict()
        )

        players.append(
            {
                "userId": user_id,
                "type": (
                    "bot"
                    if bot
                    else "human"
                ),
                "path": path,
                "events": events,
                "stats": {
                    "positions": int(
                        counts.get(
                            "Position",
                            0,
                        )
                        +
                        counts.get(
                            "BotPosition",
                            0,
                        )
                    ),
                    "kills": int(
                        counts.get(
                            "Kill",
                            0,
                        )
                    ),
                    "killed": int(
                        counts.get(
                            "Killed",
                            0,
                        )
                    ),
                    "botKills": int(
                        counts.get(
                            "BotKill",
                            0,
                        )
                    ),
                    "botKilled": int(
                        counts.get(
                            "BotKilled",
                            0,
                        )
                    ),
                    "stormDeaths": int(
                        counts.get(
                            "KilledByStorm",
                            0,
                        )
                    ),
                    "loot": int(
                        counts.get(
                            "Loot",
                            0,
                        )
                    ),
                },
            }
        )

    # ---------------------------------------------------------
    # MATCH LEVEL COUNTS
    # ---------------------------------------------------------

    human_players = [
        player
        for player in players
        if player["type"] == "human"
    ]

    bot_players = [
        player
        for player in players
        if player["type"] == "bot"
    ]

    event_counts = (
        combined["event"]
        .value_counts()
        .to_dict()
    )

    match_json = {
        "matchId": match_id,
        "cleanMatchId": clean_match_id(
            match_id
        ),
        "date": sorted(day_names)[0],
        "mapId": map_id,
        "mapDisplayName": (
            MAP_CONFIG[map_id][
                "display_name"
            ]
        ),
        "durationMs": match_duration_ms,
        "playerCount": len(players),
        "humanCount": len(human_players),
        "botCount": len(bot_players),
        "eventCounts": {
            "Position": int(
                event_counts.get(
                    "Position",
                    0,
                )
            ),
            "BotPosition": int(
                event_counts.get(
                    "BotPosition",
                    0,
                )
            ),
            "Kill": int(
                event_counts.get(
                    "Kill",
                    0,
                )
            ),
            "Killed": int(
                event_counts.get(
                    "Killed",
                    0,
                )
            ),
            "BotKill": int(
                event_counts.get(
                    "BotKill",
                    0,
                )
            ),
            "BotKilled": int(
                event_counts.get(
                    "BotKilled",
                    0,
                )
            ),
            "KilledByStorm": int(
                event_counts.get(
                    "KilledByStorm",
                    0,
                )
            ),
            "Loot": int(
                event_counts.get(
                    "Loot",
                    0,
                )
            ),
        },
        "players": players,
    }

    return match_json


def build_index(match_summaries):

    maps = sorted(
        set(
            item["mapId"]
            for item in match_summaries
        )
    )

    dates = sorted(
        set(
            item["date"]
            for item in match_summaries
        )
    )

    return {
        "metadata": {
            "totalMatches": len(
                match_summaries
            ),
            "maps": maps,
            "dates": dates,
        },
        "matches": match_summaries,
    }


def main():

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    MATCH_OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    matches = load_all_files()

    print(
        f"\nFound {len(matches)} unique matches."
    )

    summaries = []

    for index, (
        match_id,
        player_files,
    ) in enumerate(
        sorted(matches.items()),
        start=1,
    ):

        print(
            f"[{index}/{len(matches)}] "
            f"Processing {match_id}"
        )

        match_data = build_match(
            match_id,
            player_files,
        )

        filename = (
            f"{clean_match_id(match_id)}.json"
        )

        output_path = (
            MATCH_OUTPUT_ROOT
            / filename
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                match_data,
                file,
                separators=(",", ":"),
            )

        summaries.append(
            {
                "matchId": match_data[
                    "matchId"
                ],
                "cleanMatchId": match_data[
                    "cleanMatchId"
                ],
                "date": match_data[
                    "date"
                ],
                "mapId": match_data[
                    "mapId"
                ],
                "mapDisplayName": (
                    match_data[
                        "mapDisplayName"
                    ]
                ),
                "durationMs": match_data[
                    "durationMs"
                ],
                "playerCount": match_data[
                    "playerCount"
                ],
                "humanCount": match_data[
                    "humanCount"
                ],
                "botCount": match_data[
                    "botCount"
                ],
                "eventCounts": match_data[
                    "eventCounts"
                ],
                "file": (
                    f"matches/{filename}"
                ),
            }
        )

    index_data = build_index(
        summaries
    )

    index_path = (
        OUTPUT_ROOT
        / "index.json"
    )

    with index_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            index_data,
            file,
            separators=(",", ":"),
        )

    print("\n")
    print("=" * 80)
    print("PREPROCESSING COMPLETED")
    print("=" * 80)

    print(
        "Matches generated:",
        len(summaries),
    )

    print(
        "Index:",
        index_path,
    )

    print(
        "Match files:",
        MATCH_OUTPUT_ROOT,
    )


if __name__ == "__main__":
    main()