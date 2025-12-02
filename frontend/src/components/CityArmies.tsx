/**
 * City Armies Component
 * Displays the armies currently stationed in a city
 */

import React from "react";
import { Army } from "../types/gameState";
import "./styles/CityArmies.css";

interface Props {
  armies?: Army[];
  cityName?: string;
}

const CityArmies: React.FC<Props> = ({ armies, cityName }) => {
  if (!armies || armies.length === 0) {
    return (
      <div className="city-armies">
        <h3>🎖️ Stationed Forces</h3>
        <div className="no-armies">No armies stationed</div>
      </div>
    );
  }

  return (
    <div className="city-armies">
      <h3>🎖️ Stationed Forces ({armies.length})</h3>
      <div className="armies-list-container">
        {armies.map((army) => {
          const hpPercentage = army.max_hp > 0 ? (army.current_hp / army.max_hp) * 100 : 0;
          const moraleStatus =
            army.morale >= 75
              ? "Excellent"
              : army.morale >= 50
              ? "Good"
              : army.morale >= 25
              ? "Poor"
              : "Critical";

          return (
            <div key={army.id} className="army-entry">
              <div className="army-header-row">
                <span className="army-name">{army.name || `Army ${army.id.substring(0, 8)}`}</span>
                <span className="army-size">{army.unit_count} units</span>
              </div>

              <div className="army-details-grid">
                <div className="detail-item">
                  <span className="detail-label">HP:</span>
                  <span className="detail-value">
                    {army.current_hp.toFixed(0)} / {army.max_hp}
                  </span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">DMG/tick:</span>
                  <span className="detail-value">{army.damage_per_tick.toFixed(1)}</span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">Morale:</span>
                  <span className={`morale-value morale-${moraleStatus.toLowerCase()}`}>
                    {army.morale.toFixed(0)}% - {moraleStatus}
                  </span>
                </div>
              </div>

              {army.units && army.units.length > 0 && (
                <div className="unit-composition">
                  <span className="composition-label">Units:</span>
                  <div className="units-breakdown">
                    {army.units.map((unit, idx) => (
                      <span key={idx} className="unit-type">
                        {unit.type}×{unit.count}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="hp-bar">
                <div
                  className="hp-fill"
                  style={{
                    width: `${hpPercentage}%`,
                    backgroundColor:
                      hpPercentage > 75
                        ? "#27ae60"
                        : hpPercentage > 50
                        ? "#f39c12"
                        : hpPercentage > 25
                        ? "#e67e22"
                        : "#e74c3c",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CityArmies;
