/**
 * Empire Stats Component
 * Displays top-level empire statistics
 */

import React from "react";
import { EmpireData } from "../types/gameState";
import "./styles/EmpireStats.css";

interface Props {
  empire: EmpireData;
  currentTick: number;
}

const EmpireStats: React.FC<Props> = ({ empire, currentTick }) => {
  return (
    <div className="empire-stats">
      <div className="empire-header">
        <h1>{empire.name}</h1>
        <span className="tick-counter">Tick: {currentTick}</span>
      </div>

      <div className="empire-info-grid">
        <div className="info-card">
          <div className="info-label">Ideology</div>
          <div className="info-value">{empire.ideology}</div>
        </div>

        <div className="info-card">
          <div className="info-label">Capital</div>
          <div className="info-value">{empire.capital_name}</div>
        </div>

        <div className="info-card">
          <div className="info-label">Cities</div>
          <div className="info-value">{empire.cities.length}</div>
        </div>

        <div className="info-card">
          <div className="info-label">Knowledge</div>
          <div className="info-value">{empire.knowledge}</div>
        </div>
      </div>

      <div className="aggregate-stats">
        <div className="stat-row">
          <span className="stat-label">Total Population:</span>
          <span className="stat-value">{empire.total_population.total}</span>
          <span className="stat-detail">
            ({empire.total_population.employable} employable)
          </span>
        </div>

        <div className="resources-summary">
          <span className="label">Resources:</span>
          <div className="resource-items">
            <div className="resource-item">
              <span className="emoji">🍞</span>
              <span>{empire.total_resources.food}</span>
            </div>
            <div className="resource-item">
              <span className="emoji">🌲</span>
              <span>{empire.total_resources.timber}</span>
            </div>
            <div className="resource-item">
              <span className="emoji">⛏️</span>
              <span>{empire.total_resources.metal}</span>
            </div>
            <div className="resource-item">
              <span className="emoji">💰</span>
              <span>{empire.total_resources.wealth}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmpireStats;