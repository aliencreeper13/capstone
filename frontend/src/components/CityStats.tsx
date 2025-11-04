/**
 * City Stats Component
 * Displays city-level statistics
 */

import React from "react";
import { CityData } from "../types/gameState";
import "./styles/CityStats.css";

interface Props {
  city: CityData;
}

const CityStats: React.FC<Props> = ({ city }) => {
  const moraleStatus =
    city.morale > 75
      ? "Excellent"
      : city.morale > 50
      ? "Good"
      : city.morale > 25
      ? "Poor"
      : "Critical";

  const getMoraleColor = () => {
    if (city.morale > 75) return "#27ae60";
    if (city.morale > 50) return "#f39c12";
    if (city.morale > 25) return "#e74c3c";
    return "#c0392b";
  };

  const hpPercentage = (city.hitpoints / city.max_hitpoints) * 100;
  const defenseLevel =
    city.defense > 500 ? "Fortified" : city.defense > 200 ? "Protected" : "Vulnerable";

  return (
    <div className="city-stats">
      <div className="city-header">
        <h2>{city.name}</h2>
        <span className="city-coords">
          Coordinates: ({city.coords[0]}, {city.coords[1]})
        </span>
      </div>

      <div className="stats-grid">
        {/* Population Stats */}
        <div className="stat-section">
          <h3>Population</h3>
          <div className="stat-row">
            <span>Total:</span>
            <span className="value">{city.population.total}</span>
          </div>
          <div className="stat-row">
            <span>Employable:</span>
            <span className="value">{city.population.employable}</span>
          </div>
          <div className="stat-row">
            <span>Employed:</span>
            <span className="value">{city.population.employed}</span>
          </div>
        </div>

        {/* Morale */}
        <div className="stat-section morale-section">
          <h3>Morale</h3>
          <div className="morale-bar">
            <div
              className="morale-fill"
              style={{
                width: `${city.morale}%`,
                backgroundColor: getMoraleColor(),
              }}
            />
          </div>
          <div className="morale-text">
            <span className="value">{city.morale.toFixed(1)}</span>
            <span className="status">({moraleStatus})</span>
          </div>
        </div>

        {/* Defense & Health */}
        <div className="stat-section">
          <h3>Defense & Health</h3>
          <div className="stat-row">
            <span>Defense:</span>
            <span className="value">{city.defense.toFixed(0)}</span>
            <span className="detail">({defenseLevel})</span>
          </div>
          <div className="stat-row">
            <span>Health:</span>
            <span className="value">
              {city.hitpoints.toFixed(0)} / {city.max_hitpoints}
            </span>
          </div>
          <div className="hp-bar">
            <div
              className="hp-fill"
              style={{
                width: `${hpPercentage}%`,
                backgroundColor: hpPercentage > 50 ? "#27ae60" : "#e74c3c",
              }}
            />
          </div>
        </div>

        {/* Space Usage */}
        <div className="stat-section">
          <h3>Space</h3>
          <div className="stat-row">
            <span>Used:</span>
            <span className="value">
              {city.space_used} / {city.space_total}
            </span>
          </div>
          <div className="space-bar">
            <div
              className="space-fill"
              style={{
                width: `${(city.space_used / city.space_total) * 100}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Resources */}
      <div className="resources-section">
        <h3>Resources</h3>
        <div className="resources-grid">
          {[
            { name: "Food", icon: "🍞", value: city.resources.food, capacity: city.resource_capacities.food },
            { name: "Timber", icon: "🌲", value: city.resources.timber, capacity: city.resource_capacities.timber },
            { name: "Metal", icon: "⛏️", value: city.resources.metal, capacity: city.resource_capacities.metal },
            { name: "Wealth", icon: "💰", value: city.resources.wealth, capacity: city.resource_capacities.wealth },
          ].map((resource) => (
            <div key={resource.name} className="resource-card">
              <div className="resource-name">
                <span className="emoji">{resource.icon}</span>
                <span>{resource.name}</span>
              </div>
              <div className="resource-value">
                {resource.value.toFixed(0)} / {resource.capacity}
              </div>
              <div className="resource-bar">
                <div
                  className="resource-fill"
                  style={{
                    width: `${(resource.value / resource.capacity) * 100}%`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CityStats;