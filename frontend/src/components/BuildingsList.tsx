/**
 * Buildings List Component
 * Displays buildings in a city
 */

import React from "react";
import { Building } from "../types/gameState";
import "./styles/BuildingsList.css";

interface Props {
  buildings: Building[];
}

const BuildingIcons: Record<string, string> = {
  farm: "🌾",
  farm_field: "🌾",
  housing: "🏠",
  house: "🏠",
  barracks: "⚔️",
  school: "📚",
  university: "🎓",
  market: "🏪",
  temple: "⛪",
  tower: "🗼",
  wall: "🧱",
  mill: "🏭",
  forge: "🔨",
  library: "📖",
  academy: "🏫",
  default: "🏗️",
};

const getBuildingIcon = (name: string): string => {
  const normalized = name.toLowerCase();
  return (
    BuildingIcons[normalized] ||
    Object.entries(BuildingIcons).find(([key]) => normalized.includes(key))?.[1] ||
    BuildingIcons.default
  );
};

const BuildingsList: React.FC<Props> = ({ buildings }) => {
  if (buildings.length === 0) {
    return (
      <div className="buildings-list">
        <h3>Buildings</h3>
        <div className="empty-state">No buildings yet</div>
      </div>
    );
  }

  // Group buildings by name
  const groupedBuildings = buildings.reduce(
    (acc, building) => {
      const existing = acc.find((g) => g.name === building.name);
      if (existing) {
        existing.count += 1;
        existing.levels.push(building.level);
      } else {
        acc.push({
          name: building.name,
          count: 1,
          levels: [building.level],
          space_total: building.space_used,
        });
      }
      return acc;
    },
    [] as Array<{
      name: string;
      count: number;
      levels: number[];
      space_total: number;
    }>
  );

  return (
    <div className="buildings-list">
      <h3>Buildings ({buildings.length})</h3>
      <div className="buildings-container">
        {groupedBuildings.map((group) => (
          <div key={group.name} className="building-group">
            <div className="building-header">
              <span className="icon">{getBuildingIcon(group.name)}</span>
              <span className="name">{group.name}</span>
              <span className="count">x{group.count}</span>
            </div>
            <div className="building-levels">
              {group.levels.map((level, idx) => (
                <span key={idx} className="level-badge">
                  Lv.{level}
                </span>
              ))}
            </div>
            <div className="space-info">Space: {group.space_total}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BuildingsList;