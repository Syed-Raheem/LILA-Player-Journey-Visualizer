from pathlib import Path
from collections import Counter

import pyarrow.parquet as pq


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "player_data"


def decode_value(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")

    return value


def is_bot(user_id: str) -> bool:
    return str(user_id).isdigit()


def main():

    print("=" * 80)
    print("MOVEMENT EVENT CLASSIFICATION CHECK")
    print("=" * 80)

    counts = Counter()

    for day_folder in sorted(DATA_ROOT.glob("February_*")):

        print(f"\nChecking {day_folder.name}...")

        for file_path in sorted(
            day_folder.glob("*.nakama-0")
        ):

            table = pq.read_table(
                file_path,
                columns=[
                    "user_id",
                    "event",
                ],
            )

            df = table.to_pandas()

            df["user_id"] = (
                df["user_id"]
                .apply(decode_value)
                .astype(str)
            )

            df["event"] = (
                df["event"]
                .apply(decode_value)
                .astype(str)
            )

            movement_rows = df[
                df["event"].isin(
                    [
                        "Position",
                        "BotPosition",
                    ]
                )
            ]

            for row in movement_rows.itertuples(
                index=False
            ):

                player_type = (
                    "bot"
                    if is_bot(row.user_id)
                    else "human"
                )

                counts[
                    (
                        player_type,
                        row.event,
                    )
                ] += 1

    print("\n")
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)

    human_position = counts[
        ("human", "Position")
    ]

    human_bot_position = counts[
        ("human", "BotPosition")
    ]

    bot_position = counts[
        ("bot", "Position")
    ]

    bot_bot_position = counts[
        ("bot", "BotPosition")
    ]

    print("\nHUMAN IDs")
    print("-" * 50)

    print(
        "Position:    ",
        human_position,
    )

    print(
        "BotPosition: ",
        human_bot_position,
    )

    print("\nBOT IDs")
    print("-" * 50)

    print(
        "Position:    ",
        bot_position,
    )

    print(
        "BotPosition: ",
        bot_bot_position,
    )

    total = (
        human_position
        + human_bot_position
        + bot_position
        + bot_bot_position
    )

    mismatched = (
        human_bot_position
        + bot_position
    )

    print("\nTOTAL")
    print("-" * 50)

    print(
        "Movement rows:",
        total,
    )

    print(
        "Unexpected movement event/player combinations:",
        mismatched,
    )

    print("\nExpected raw movement rows: 73059")

    print("\n")
    print("=" * 80)
    print("CHECK COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()