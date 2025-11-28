/**
 * Event Feed Component
 * Displays recent game events (battles, construction, resources, etc.)
 */

import React from "react";
import "./styles/EventFeed.css";

interface GameEvent {
  type: string;
  unix_timestamp: number;
  source: string;
  description: string;
  data: Record<string, any>;
}

interface Props {
  events: GameEvent[];
  maxVisible?: number;
}

const EventTypeIcons: Record<string, string> = {
  battle_tick: "⚔️",
  battle_result: "🏆",
  city_captured: "🏰",
  job_submission: "🛠️",
  building_completed: "✅",
  upgrade_completed: "✅",
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
  // Show newest events first
  const visibleEvents = events.slice(0, maxVisible);

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
      <h3>
        📰 Event Log {events.length > maxVisible && `(showing ${maxVisible}/${events.length})`}
      </h3>
      <div className="events-list">
        {visibleEvents.map((event, index) => (
          <div key={index} className="event-item">
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
      {events.length > maxVisible && (
        <div className="more-events">
          +{events.length - maxVisible} more event{events.length - maxVisible !== 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
};

export default EventFeed;