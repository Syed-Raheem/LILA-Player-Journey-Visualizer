export type PlayerType = "human" | "bot";

export interface EventCounts {
  Position: number;
  BotPosition: number;
  Kill: number;
  Killed: number;
  BotKill: number;
  BotKilled: number;
  KilledByStorm: number;
  Loot: number;
}

export interface MatchSummary {
  matchId: string;
  cleanMatchId: string;
  date: string;
  mapId: string;
  mapDisplayName: string;
  durationMs: number;
  playerCount: number;
  humanCount: number;
  botCount: number;
  eventCounts: EventCounts;
  file: string;
}

export interface IndexMetadata {
  totalMatches: number;
  maps: string[];
  dates: string[];
}

export interface TelemetryIndex {
  metadata: IndexMetadata;
  matches: MatchSummary[];
}

export interface PositionPoint {
  t: number;
  x: number;
  y: number;
  z: number;
  u: number;
  v: number;
  px: number;
  py: number;
}

export type PlayerEventType =
  | "Kill"
  | "Killed"
  | "BotKill"
  | "BotKilled"
  | "KilledByStorm"
  | "Loot";

export interface PlayerEvent {
  type: PlayerEventType;
  t: number;
  x: number;
  y: number;
  z: number;
  u: number;
  v: number;
  px: number;
  py: number;
}

export interface PlayerStats {
  positions: number;
  kills: number;
  killed: number;
  botKills: number;
  botKilled: number;
  stormDeaths: number;
  loot: number;
}

export interface PlayerJourney {
  userId: string;
  type: PlayerType;
  path: PositionPoint[];
  events: PlayerEvent[];
  stats: PlayerStats;
}

export interface MatchData {
  matchId: string;
  cleanMatchId: string;
  date: string;
  mapId: string;
  mapDisplayName: string;
  durationMs: number;
  playerCount: number;
  humanCount: number;
  botCount: number;
  eventCounts: EventCounts;
  players: PlayerJourney[];
}