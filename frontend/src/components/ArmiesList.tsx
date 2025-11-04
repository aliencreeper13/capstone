/**
 * Armies List Component
 * Displays armies stationed in a city
 */

import React from "react";
import { Army } from "../types/gameState";
import "./styles/ArmiesList.css";

interface Props {
  armies: Army[];
}

const ArmiesList: React.FC<Props> = ({ armies }) => {
  if (armies.length === 0) {
    return (
      <div className="armies-list">
        <h3>Armies</h3>
        <div className="empty-state">No armies stationed here</div>
      </div>
    );
  }

  return (
    <div className="armies-list">
      <h3>Armies ({armies.length})</h3>
      <div className="armies-container">
        {armies.map((army) => {
          const hpPercentage = (army.current_hp / army.max_hp) * 100;
          const healthStatus =
            hpPercentage > 75
              ? "Healthy"
              : hpPercentage > 50
              ? "Wounded"
              : hpPercentage > 25
              ? "Damaged"
              : "Critical";

          return (
            <div key={army.id} className="army-card">
              <div className="army-header">
                <h4>{army.name}</h4>
                <span className="army-id">#{army.id}</span>
              </div>

              <div className="army-stats">
                <div className="stat-row">
                  <span className="label">Units:</span>
                  <span className="value">{army.unit_count}</span>
                </div>

                <div className="stat-row">
                  <span className="label">Damage/Tick:</span>
                  <span className="value">{army.damage_per_tick.toFixed(1)}</span>
                </div>

                <div className="stat-row">
                  <span className="label">Health:</span>
                  <span className="value">
                    {army.current_hp.toFixed(0)} / {army.max_hp}
                  </span>
                  <span className="status">({healthStatus})</span>
                </div>

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
                          ? "#e74c3c"
                          : "#c0392b",
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ArmiesList;