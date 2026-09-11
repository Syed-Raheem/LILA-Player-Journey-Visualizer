from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_ROOT = (
    PROJECT_ROOT
    / "processed_data"
)

MATCH_ROOT = (
    OUTPUT_ROOT
    / "matches"
)


def main():

    print("=" * 80)
    print("PROCESSED DATA VALIDATION")
    print("=" * 80)

    index_path = (
        OUTPUT_ROOT
        / "index.json"
    )

    if not index_path.exists():
        raise FileNotFoundError(
            "index.json does not exist."
        )

    with index_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        index = json.load(file)

    matches = index["matches"]

    print(
        "\nMatches in index:",
        len(matches),
    )

    json_files = list(
        MATCH_ROOT.glob("*.json")
    )

    print(
        "Match JSON files:",
        len(json_files),
    )

    missing_files = []

    invalid_positions = []

    total_players = 0
    total_humans = 0
    total_bots = 0

    total_paths = 0
    total_events = 0

    for match in matches:

        path = (
            OUTPUT_ROOT
            / match["file"]
        )

        if not path.exists():

            missing_files.append(
                match["file"]
            )

            continue

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        for player in data["players"]:

            total_players += 1

            if player["type"] == "bot":
                total_bots += 1
            else:
                total_humans += 1

            for point in player["path"]:

                total_paths += 1

                if not (
                    0 <= point["u"] <= 1
                    and
                    0 <= point["v"] <= 1
                ):

                    invalid_positions.append(
                        {
                            "match": data[
                                "matchId"
                            ],
                            "user": player[
                                "userId"
                            ],
                            "u": point["u"],
                            "v": point["v"],
                        }
                    )

            total_events += len(
                player["events"]
            )

    print("\nPLAYER JOURNEYS")
    print("-" * 50)

    print(
        "Player-match journeys:",
        total_players,
    )

    print(
        "Human journeys:",
        total_humans,
    )

    print(
        "Bot journeys:",
        total_bots,
    )

    print("\nDATA POINTS")
    print("-" * 50)

    print(
        "Movement points:",
        total_paths,
    )

    print(
        "Marker events:",
        total_events,
    )

    print("\nVALIDATION")
    print("-" * 50)

    print(
        "Missing match files:",
        len(missing_files),
    )

    print(
        "Invalid minimap positions:",
        len(invalid_positions),
    )

    if missing_files:

        print(
            "\nMissing files:"
        )

        for item in missing_files[:10]:
            print(item)

    if invalid_positions:

        print(
            "\nInvalid position examples:"
        )

        for item in (
            invalid_positions[:10]
        ):

            print(item)

    print("\n")
    print("=" * 80)

    if (
        len(matches) == 796
        and
        len(json_files) == 796
        and
        not missing_files
        and
        not invalid_positions
    ):

        print(
            "VALIDATION PASSED"
        )

    else:

        print(
            "VALIDATION NEEDS REVIEW"
        )

    print("=" * 80)


if __name__ == "__main__":
    main()