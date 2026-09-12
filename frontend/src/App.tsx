import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Bot,
  CalendarDays,
  Crosshair,
  Map,
  Pause,
  Play,
  RotateCcw,
  Skull,
  Users,
} from "lucide-react";

import "./App.css";

import {
  loadMatchData,
  loadTelemetryIndex,
} from "./data/telemetry";

import type {
  MatchData,
  MatchSummary,
  TelemetryIndex,
} from "./types/telemetry";

import {
  MINIMAP_PATHS,
} from "./utils/minimaps";

function formatTime(
  milliseconds: number
) {
  const totalSeconds =
    Math.floor(
      milliseconds / 1000
    );

  const minutes =
    Math.floor(
      totalSeconds / 60
    );

  const seconds =
    totalSeconds % 60;

  return `${minutes}:${seconds
    .toString()
    .padStart(2, "0")}`;
}

function App() {
  const [
    telemetryIndex,
    setTelemetryIndex,
  ] = useState<TelemetryIndex | null>(
    null
  );

  const [
    selectedMap,
    setSelectedMap,
  ] = useState("");

  const [
    selectedDate,
    setSelectedDate,
  ] = useState("");

  const [
    selectedMatchId,
    setSelectedMatchId,
  ] = useState("");

  const [
    matchData,
    setMatchData,
  ] = useState<MatchData | null>(
    null
  );

  const [
    loadingMatch,
    setLoadingMatch,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null
  );

  const [
    showHumans,
    setShowHumans,
  ] = useState(true);

  const [
    showBots,
    setShowBots,
  ] = useState(true);

  const [
    showKills,
    setShowKills,
  ] = useState(true);

  const [
    showDeaths,
    setShowDeaths,
  ] = useState(true);

  const [
    showLoot,
    setShowLoot,
  ] = useState(true);

  const [
    showStormDeaths,
    setShowStormDeaths,
  ] = useState(true);

  const [
    currentTimeMs,
    setCurrentTimeMs,
  ] = useState(0);

  const [
    isPlaying,
    setIsPlaying,
  ] = useState(false);

  const [
    playbackSpeed,
    setPlaybackSpeed,
  ] = useState(1);

  useEffect(() => {
    async function initialise() {
      try {
        const index =
          await loadTelemetryIndex();

        setTelemetryIndex(index);

        const firstMatch =
          index.matches[0];

        if (firstMatch) {
          setSelectedMap(
            firstMatch.mapId
          );

          setSelectedDate(
            firstMatch.date
          );

          setSelectedMatchId(
            firstMatch.matchId
          );
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to initialise application."
        );
      }
    }

    initialise();
  }, []);

  const filteredMatches =
    useMemo(() => {
      if (!telemetryIndex) {
        return [];
      }

      return telemetryIndex.matches.filter(
        (match) => {
          const mapMatches =
            !selectedMap ||
            match.mapId ===
              selectedMap;

          const dateMatches =
            !selectedDate ||
            match.date ===
              selectedDate;

          return (
            mapMatches &&
            dateMatches
          );
        }
      );
    }, [
      telemetryIndex,
      selectedMap,
      selectedDate,
    ]);

  useEffect(() => {
    if (!telemetryIndex) {
      return;
    }

    const selectedStillExists =
      filteredMatches.some(
        (match) =>
          match.matchId ===
          selectedMatchId
      );

    if (selectedStillExists) {
      return;
    }

    if (
      filteredMatches.length > 0
    ) {
      setSelectedMatchId(
        filteredMatches[0]
          .matchId
      );
    } else {
      setSelectedMatchId("");
    }
  }, [
    telemetryIndex,
    filteredMatches,
    selectedMatchId,
  ]);

  const selectedSummary:
    | MatchSummary
    | undefined =
    filteredMatches.find(
      (match) =>
        match.matchId ===
        selectedMatchId
    );

  useEffect(() => {
    let cancelled = false;

    async function fetchMatch() {
      if (!selectedSummary) {
        setMatchData(null);
        setLoadingMatch(false);
        setCurrentTimeMs(0);
        setIsPlaying(false);
        return;
      }

      setLoadingMatch(true);
      setIsPlaying(false);

      try {
        const data =
          await loadMatchData(
            selectedSummary.file
          );

        if (!cancelled) {
          setMatchData(data);

          setCurrentTimeMs(
            data.durationMs
          );
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load match."
          );
        }
      } finally {
        if (!cancelled) {
          setLoadingMatch(false);
        }
      }
    }

    fetchMatch();

    return () => {
      cancelled = true;
    };
  }, [selectedSummary]);

  useEffect(() => {
    if (
      !isPlaying ||
      !matchData ||
      matchData.durationMs <= 0
    ) {
      return;
    }

    let lastTimestamp:
      | number
      | null = null;

    let animationFrameId:
      | number
      | null = null;

    function animate(
      timestamp: number
    ) {
      if (lastTimestamp === null) {
        lastTimestamp =
          timestamp;
      }

      const delta =
        timestamp -
        lastTimestamp;

      lastTimestamp =
        timestamp;

      setCurrentTimeMs(
        (previousTime) => {
          if (!matchData) {
            return previousTime;
          }

          const nextTime =
            previousTime +
            delta *
              playbackSpeed;

          if (
            nextTime >=
            matchData.durationMs
          ) {
            setIsPlaying(
              false
            );

            return (
              matchData.durationMs
            );
          }

          return nextTime;
        }
      );

      animationFrameId =
        requestAnimationFrame(
          animate
        );
    }

    animationFrameId =
      requestAnimationFrame(
        animate
      );

    return () => {
      if (
        animationFrameId !==
        null
      ) {
        cancelAnimationFrame(
          animationFrameId
        );
      }
    };
  }, [
    isPlaying,
    matchData,
    playbackSpeed,
  ]);

  if (error) {
    return (
      <div className="center-screen">
        <div className="error-panel">
          <h1>
            Unable to load telemetry
          </h1>

          <p>
            {error}
          </p>
        </div>
      </div>
    );
  }

  if (!telemetryIndex) {
    return (
      <div className="center-screen">
        Loading telemetry...
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand-row">
            <span className="brand">
              LILA BLACK
            </span>

            <span className="divider">
              /
            </span>

            <span className="product-name">
              PLAYER JOURNEY
              ANALYZER
            </span>
          </div>

          <p className="subtitle">
            Level Design Telemetry
          </p>
        </div>

        <div className="dataset-pill">
          {
            telemetryIndex
              .metadata
              .totalMatches
          }{" "}
          MATCHES
        </div>
      </header>

      <section className="filter-bar">
        <label className="filter-field">
          <span>
            <Map size={14} />
            MAP
          </span>

          <select
            value={selectedMap}
            onChange={(event) =>
              setSelectedMap(
                event.target.value
              )
            }
          >
            {
              telemetryIndex
                .metadata
                .maps.map(
                  (mapId) => (
                    <option
                      key={
                        mapId
                      }
                      value={
                        mapId
                      }
                    >
                      {mapId}
                    </option>
                  )
                )
            }
          </select>
        </label>

        <label className="filter-field">
          <span>
            <CalendarDays
              size={14}
            />
            DATE
          </span>

          <select
            value={
              selectedDate
            }
            onChange={(event) =>
              setSelectedDate(
                event.target.value
              )
            }
          >
            {
              telemetryIndex
                .metadata
                .dates.map(
                  (date) => (
                    <option
                      key={
                        date
                      }
                      value={
                        date
                      }
                    >
                      {
                        date.replace(
                          "_",
                          " "
                        )
                      }
                    </option>
                  )
                )
            }
          </select>
        </label>

        <label className="filter-field match-filter">
          <span>
            MATCH
          </span>

          <select
            value={
              selectedMatchId
            }
            onChange={(event) =>
              setSelectedMatchId(
                event.target.value
              )
            }
            disabled={
              filteredMatches
                .length === 0
            }
          >
            {
              filteredMatches
                .length > 0 ? (
                filteredMatches.map(
                  (match) => (
                    <option
                      key={
                        match.matchId
                      }
                      value={
                        match.matchId
                      }
                    >
                      {
                        match.cleanMatchId
                      }
                    </option>
                  )
                )
              ) : (
                <option value="">
                  No matches
                  available
                </option>
              )
            }
          </select>
        </label>
      </section>

      <section className="layer-bar">
        <span className="layer-title">
          VISIBILITY
        </span>

        <label className="layer-toggle">
          <input
            type="checkbox"
            checked={
              showHumans
            }
            onChange={(event) =>
              setShowHumans(
                event.target.checked
              )
            }
          />

          <span className="layer-swatch human-swatch" />

          Humans
        </label>

        <label className="layer-toggle">
          <input
            type="checkbox"
            checked={
              showBots
            }
            onChange={(event) =>
              setShowBots(
                event.target.checked
              )
            }
          />

          <span className="layer-swatch bot-swatch" />

          Bots
        </label>

        <span className="layer-separator" />

        <label className="layer-toggle">
          <input
            type="checkbox"
            checked={
              showKills
            }
            onChange={(event) =>
              setShowKills(
                event.target.checked
              )
            }
          />

          <span className="event-dot kill-dot" />

          Kills
        </label>

        <label className="layer-toggle">
          <input
            type="checkbox"
            checked={
              showDeaths
            }
            onChange={(event) =>
              setShowDeaths(
                event.target.checked
              )
            }
          />

          <span className="event-dot death-dot" />

          Deaths
        </label>

        <label className="layer-toggle">
          <input
            type="checkbox"
            checked={
              showLoot
            }
            onChange={(event) =>
              setShowLoot(
                event.target.checked
              )
            }
          />

          <span className="event-dot loot-dot" />

          Loot
        </label>

        <label className="layer-toggle">
          <input
            type="checkbox"
            checked={
              showStormDeaths
            }
            onChange={(event) =>
              setShowStormDeaths(
                event.target.checked
              )
            }
          />

          <span className="event-dot storm-dot" />

          Storm
        </label>
      </section>

      <main className="workspace">
        <section className="map-panel">
          <div className="panel-header">
            <div>
              <span className="eyebrow">
                ACTIVE MAP
              </span>

              <h2>
                {
                  matchData
                    ?.mapDisplayName ??
                  "No match selected"
                }
              </h2>
            </div>

            {
              loadingMatch && (
                <span className="loading-label">
                  LOADING
                  MATCH...
                </span>
              )
            }
          </div>

          <div className="minimap-stage">
            {
              matchData ? (
                <>
                  <img
                    src={
                      MINIMAP_PATHS[
                        matchData
                          .mapId
                      ]
                    }
                    alt={
                      `${matchData.mapDisplayName} minimap`
                    }
                    className="minimap-image"
                  />

                  <svg
                    className="telemetry-layer"
                    viewBox="0 0 1024 1024"
                    preserveAspectRatio="none"
                  >
                    {
                      matchData
                        .players
                        .map(
                          (
                            player
                          ) => {
                            if (
                              player
                                .type ===
                                "human" &&
                              !showHumans
                            ) {
                              return null;
                            }

                            if (
                              player
                                .type ===
                                "bot" &&
                              !showBots
                            ) {
                              return null;
                            }

                            const visiblePath =
                              player.path.filter(
                                (
                                  point
                                ) =>
                                  point.t <=
                                  currentTimeMs
                              );

                            if (
                              visiblePath
                                .length <
                              2
                            ) {
                              return null;
                            }

                            const points =
                              visiblePath
                                .map(
                                  (
                                    point
                                  ) =>
                                    `${point.px},${point.py}`
                                )
                                .join(
                                  " "
                                );

                            return (
                              <polyline
                                key={
                                  player.userId
                                }
                                points={
                                  points
                                }
                                fill="none"
                                className={
                                  player.type ===
                                  "human"
                                    ? "human-path"
                                    : "bot-path"
                                }
                              />
                            );
                          }
                        )
                    }

                    {
                      matchData
                        .players
                        .map(
                          (
                            player
                          ) => {
                            if (
                              player
                                .type ===
                                "human" &&
                              !showHumans
                            ) {
                              return null;
                            }

                            if (
                              player
                                .type ===
                                "bot" &&
                              !showBots
                            ) {
                              return null;
                            }

                            const visiblePoints =
                              player.path.filter(
                                (
                                  point
                                ) =>
                                  point.t <=
                                  currentTimeMs
                              );

                            if (
                              visiblePoints
                                .length ===
                              0
                            ) {
                              return null;
                            }

                            const currentPoint =
                              visiblePoints[
                                visiblePoints.length -
                                  1
                              ];

                            return (
                              <circle
                                key={
                                  `current-${player.userId}`
                                }
                                cx={
                                  currentPoint.px
                                }
                                cy={
                                  currentPoint.py
                                }
                                r={
                                  player.type ===
                                  "human"
                                    ? 8
                                    : 6
                                }
                                className={
                                  player.type ===
                                  "human"
                                    ? "human-current-position"
                                    : "bot-current-position"
                                }
                              />
                            );
                          }
                        )
                    }

                    {
                      matchData
                        .players
                        .flatMap(
                          (
                            player
                          ) => {
                            if (
                              player
                                .type ===
                                "human" &&
                              !showHumans
                            ) {
                              return [];
                            }

                            if (
                              player
                                .type ===
                                "bot" &&
                              !showBots
                            ) {
                              return [];
                            }

                            return player.events.map(
                              (
                                event,
                                eventIndex
                              ) => {
                                if (
                                  event.t >
                                  currentTimeMs
                                ) {
                                  return null;
                                }

                                const isKill =
                                  event.type ===
                                    "Kill" ||
                                  event.type ===
                                    "BotKill";

                                const isDeath =
                                  event.type ===
                                    "Killed" ||
                                  event.type ===
                                    "BotKilled";

                                const isLoot =
                                  event.type ===
                                  "Loot";

                                const isStorm =
                                  event.type ===
                                  "KilledByStorm";

                                if (
                                  isKill &&
                                  !showKills
                                ) {
                                  return null;
                                }

                                if (
                                  isDeath &&
                                  !showDeaths
                                ) {
                                  return null;
                                }

                                if (
                                  isLoot &&
                                  !showLoot
                                ) {
                                  return null;
                                }

                                if (
                                  isStorm &&
                                  !showStormDeaths
                                ) {
                                  return null;
                                }

                                let className =
                                  "event-marker";

                                if (
                                  isKill
                                ) {
                                  className +=
                                    " kill-marker";
                                }

                                if (
                                  isDeath
                                ) {
                                  className +=
                                    " death-marker";
                                }

                                if (
                                  isLoot
                                ) {
                                  className +=
                                    " loot-marker";
                                }

                                if (
                                  isStorm
                                ) {
                                  className +=
                                    " storm-marker";
                                }

                                return (
                                  <circle
                                    key={
                                      `${player.userId}-${event.type}-${eventIndex}`
                                    }
                                    cx={
                                      event.px
                                    }
                                    cy={
                                      event.py
                                    }
                                    r={
                                      isStorm
                                        ? 9
                                        : 6
                                    }
                                    className={
                                      className
                                    }
                                  />
                                );
                              }
                            );
                          }
                        )
                    }
                  </svg>
                </>
              ) : (
                <div className="center-screen">
                  No match available
                  for the selected
                  filters.
                </div>
              )
            }
          </div>

          <div className="timeline-panel">
            <div className="timeline-top-row">
              <div className="timeline-time">
                <strong>
                  {
                    formatTime(
                      currentTimeMs
                    )
                  }
                </strong>

                <span>
                  /
                </span>

                <span>
                  {
                    formatTime(
                      matchData
                        ?.durationMs ??
                        0
                    )
                  }
                </span>
              </div>

              <div className="playback-speed">
                <span>
                  SPEED
                </span>

                <button
                  className={
                    playbackSpeed ===
                    0.5
                      ? "speed-button active"
                      : "speed-button"
                  }
                  onClick={() =>
                    setPlaybackSpeed(
                      0.5
                    )
                  }
                >
                  0.5×
                </button>

                <button
                  className={
                    playbackSpeed ===
                    1
                      ? "speed-button active"
                      : "speed-button"
                  }
                  onClick={() =>
                    setPlaybackSpeed(
                      1
                    )
                  }
                >
                  1×
                </button>

                <button
                  className={
                    playbackSpeed ===
                    2
                      ? "speed-button active"
                      : "speed-button"
                  }
                  onClick={() =>
                    setPlaybackSpeed(
                      2
                    )
                  }
                >
                  2×
                </button>
              </div>
            </div>

            <input
              className="timeline-slider"
              type="range"
              min={0}
              max={
                matchData
                  ?.durationMs ??
                0
              }
              step={50}
              value={
                Math.min(
                  currentTimeMs,
                  matchData
                    ?.durationMs ??
                    0
                )
              }
              onChange={(event) => {
                setCurrentTimeMs(
                  Number(
                    event.target
                      .value
                  )
                );

                setIsPlaying(
                  false
                );
              }}
            />

            <div className="playback-controls">
              <button
                className="playback-button"
                onClick={() => {
                  setCurrentTimeMs(
                    0
                  );

                  setIsPlaying(
                    false
                  );
                }}
                disabled={
                  !matchData
                }
              >
                <RotateCcw
                  size={15}
                />

                RESET
              </button>

              <button
                className="playback-button primary"
                onClick={() => {
                  if (!matchData) {
                    return;
                  }

                  if (
                    currentTimeMs >=
                    matchData
                      .durationMs
                  ) {
                    setCurrentTimeMs(
                      0
                    );
                  }

                  setIsPlaying(
                    (value) =>
                      !value
                  );
                }}
                disabled={
                  !matchData
                }
              >
                {
                  isPlaying ? (
                    <>
                      <Pause
                        size={15}
                      />
                      PAUSE
                    </>
                  ) : (
                    <>
                      <Play
                        size={15}
                      />
                      PLAY
                    </>
                  )
                }
              </button>
            </div>
          </div>
        </section>

        <aside className="sidebar">
          <div className="sidebar-heading">
            MATCH OVERVIEW
          </div>

          <div className="stat-grid">
            <div className="stat-card">
              <Users
                size={18}
              />

              <span>
                HUMANS
              </span>

              <strong>
                {
                  matchData
                    ?.humanCount ??
                  "-"
                }
              </strong>
            </div>

            <div className="stat-card">
              <Bot
                size={18}
              />

              <span>
                BOTS
              </span>

              <strong>
                {
                  matchData
                    ?.botCount ??
                  "-"
                }
              </strong>
            </div>

            <div className="stat-card">
              <Crosshair
                size={18}
              />

              <span>
                KILLS
              </span>

              <strong>
                {
                  matchData
                    ? (
                        matchData
                          .eventCounts
                          .Kill +
                        matchData
                          .eventCounts
                          .BotKill
                      )
                    : "-"
                }
              </strong>
            </div>

            <div className="stat-card">
              <Skull
                size={18}
              />

              <span>
                DEATHS
              </span>

              <strong>
                {
                  matchData
                    ? (
                        matchData
                          .eventCounts
                          .Killed +
                        matchData
                          .eventCounts
                          .BotKilled +
                        matchData
                          .eventCounts
                          .KilledByStorm
                      )
                    : "-"
                }
              </strong>
            </div>
          </div>

          <div className="legend-card">
            <span className="eyebrow">
              JOURNEY & EVENT
              LEGEND
            </span>

            <div className="legend-row">
              <span className="line human-line" />
              Human journey
            </div>

            <div className="legend-row">
              <span className="line bot-line" />
              Bot journey
            </div>

            <div className="legend-row">
              <span className="legend-event kill-dot" />
              Kill
            </div>

            <div className="legend-row">
              <span className="legend-event death-dot" />
              Death
            </div>

            <div className="legend-row">
              <span className="legend-event loot-dot" />
              Loot
            </div>

            <div className="legend-row">
              <span className="legend-event storm-dot" />
              Storm death
            </div>
          </div>

          <div className="match-details">
            <span className="eyebrow">
              MATCH
            </span>

            <code>
              {
                matchData
                  ?.cleanMatchId ??
                "-"
              }
            </code>
          </div>
        </aside>
      </main>
    </div>
  );
}

export default App;