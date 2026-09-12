import type {
  MatchData,
  TelemetryIndex,
} from "../types/telemetry";

export async function loadTelemetryIndex(): Promise<TelemetryIndex> {
  const response = await fetch("/data/index.json");

  if (!response.ok) {
    throw new Error(
      `Failed to load telemetry index: ${response.status}`
    );
  }

  return response.json();
}

export async function loadMatchData(
  file: string
): Promise<MatchData> {
  const response = await fetch(`/data/${file}`);

  if (!response.ok) {
    throw new Error(
      `Failed to load match data: ${response.status}`
    );
  }

  return response.json();
}