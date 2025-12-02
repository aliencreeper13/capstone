/**
 * Event Feed Component
 * Displays recent game events with filtering for human vs AI actions
 */

import React, { useState, useMemo } from "react";
import "./styles/EventFeed.css";

interface GameEvent {
  type: string;
  unix_timestamp: number;
  source: string;
  description: string;
  data: Record<string, any>;
  triggered_by_ai?: boolean;
}

interface Props {
  events: GameEvent[];
  maxVisible?: number;
}

type FilterTab = "all" | "human" | "ai";

const EventTypeIcons: Record<string, string> = {
  battle_tick: "⚔️",
  battle_result: "🏆",
  city_captured: "🏰",
  job_submission: "🛠️",
  building_completed: "✅",
  upgrade_completed: "✅",
  building_failed: "❌",
  upgrade_failed: "❌",
  unit_created: "👥",
  resource_change: "📦",
  custom: "📜",
  default: "•",
};

const EventTypeColors: Record<string, string> = {
  battle_tick: "#e74c3c",
  battle_result: "#c0392b",
  city_captured: "#9b59b6",
  building_completed: "#27ae60",
  upgrade_completed: "#27ae60",
  job_submission: "#f1c40f",
  unit_created: "#3498db",
  resource_change: "#f39c12",
  custom: "#95a5a6",
  default: "#bdc3c7",
};

const getEventIcon = (type: string): string => {
  return EventTypeIcons[type] || EventTypeIcons.default;
};

const getEventColor = (type: string): string => {
  return EventTypeColors[type] || EventTypeColors.default;
};

const getSourceBadge = (triggered_by_ai?: boolean): string => {
  return triggered_by_ai ? "🤖" : "👤";
};

const formatTimestamp = (unix_timestamp: number): string => {
  const date = new Date(unix_timestamp * 1000);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);

  if (diffSecs < 60) return `${diffSecs}s ago`;
  if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ago`;
  if (diffSecs < 86400) return `${Math.floor(diffSecs / 3600)}h ago`;
  
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const EventFeed: React.FC<Props> = ({ events, maxVisible = 10 }) => {
  const [activeTab, setActiveTab] = useState<FilterTab>("all");

  const filteredEvents = useMemo(() => {
    switch (activeTab) {
      case "human":
        return events.filter(e => !e.triggered_by_ai);
      case "ai":
        return events.filter(e => e.triggered_by_ai);
      case "all":
      default:
        return events;
    }
  }, [events, activeTab]);

  const eventCounts = useMemo(() => ({
    all: events.length,
    human: events.filter(e => !e.triggered_by_ai).length,
    ai: events.filter(e => e.triggered_by_ai).length,
  }), [events]);

  const visibleEvents = filteredEvents.slice(0, maxVisible);

  if (events.length === 0) {
    return (
      <div className="event-feed">
        <h3>📰 Event Log</h3>
        <div className="empty-state">No events yet</div>
      </div>
    );
  }

  return (
    <div className="event-feed">
      <h3>📰 Event Log</h3>
      
      <div className="event-feed-header">
        <div className="event-tabs">
          <button
            className={`tab ${activeTab === "all" ? "active" : ""}`}
            onClick={() => setActiveTab("all")}
          >
            All Events ({eventCounts.all})
          </button>
          <button
            className={`tab ${activeTab === "human" ? "active" : ""}`}
            onClick={() => setActiveTab("human")}
          >
            👤 Human ({eventCounts.human})
          </button>
          <button
            className={`tab ${activeTab === "ai" ? "active" : ""}`}
            onClick={() => setActiveTab("ai")}
          >
            🤖 AI ({eventCounts.ai})
          </button>
        </div>
      </div>

      {filteredEvents.length === 0 ? (
        <div className="empty-state">
          No {activeTab === "all" ? "" : activeTab} events yet
        </div>
      ) : (
        <>
          <div className="events-list">
            {visibleEvents.map((event, index) => (
              <div key={index} className="event-item">
                <div className="event-source-badge">
                  {getSourceBadge(event.triggered_by_ai)}
                </div>
                <div className="event-icon" style={{ color: getEventColor(event.type) }}>
                  {getEventIcon(event.type)}
                </div>
                <div className="event-content">
                  <div className="event-description">{event.description}</div>
                  <div className="event-meta">
                    <span className="event-type" style={{ color: getEventColor(event.type) }}>
                      {event.type.replace(/_/g, " ")}
                    </span>
                    <span className="event-time">{formatTimestamp(event.unix_timestamp)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {filteredEvents.length > maxVisible && (
            <div className="more-events">
              +{filteredEvents.length - maxVisible} more event{filteredEvents.length - maxVisible !== 1 ? "s" : ""}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default EventFeed;
