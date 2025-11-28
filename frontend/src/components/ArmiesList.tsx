/**
 * Armies List Component - Phase 4 Update
 * Displays armies across the entire map with location and movement status
 */

import React from "react";
import { Army } from "../types/gameState";
import "./styles/ArmiesList.css";

interface Props {
  armies?: Army[];
  onArmySelect?: (armyId: string) => void;
  selectedArmyId?: string | null;
}

const ArmiesList: React.FC<Props> = ({ armies, onArmySelect, selectedArmyId }) => {
  if (!armies || armies.length === 0) {
    return (
      <div className="armies-list">
        <h3>Armies</h3>
        <div className="empty-state">No armies found</div>
      </div>
    );
  }

  return (
    <div className="armies-list">
      <h3>Armies ({armies.length})</h3>
      <div className="armies-container">
        {armies.map((army) => {
          const hpPercentage = (army.current_hp / army.max_hp) * 100;
          const hpPercentageMinusNeutral = (hpPercentage - 50);
          
          const healthStatus = hpPercentageMinusNeutral >= 33.33
            ? 'Locked in'
            : hpPercentageMinusNeutral >= 16.66 && hpPercentageMinusNeutral < 33.33
            ? 'Excellent'
            : hpPercentageMinusNeutral >= -16.66 && hpPercentageMinusNeutral < 16.66
            ? 'Healthy'
            : hpPercentageMinusNeutral >= -33.33 && hpPercentageMinusNeutral < -16.66
            ? 'Damaged'
            : 'Critical'
            
          const isSelected = selectedArmyId === army.id;
          const isMoving = army.destination !== undefined && army.destination !== null;

          return (
            <div 
              key={army.id} 
              className={`army-card ${isSelected ? 'selected' : ''} ${isMoving ? 'moving' : ''}`}
              onClick={() => onArmySelect && onArmySelect(army.id)}
            >
              <div className="army-header">
                <h4>{army.name}</h4>
                <span className="army-id">#{army.id.substring(0, 8)}</span>
                {isMoving && <span className="moving-badge">Moving</span>}
              </div>

              <div className="army-location">
                <span className="label">Location:</span>
                <span className="location-value">{army.location}</span>
                {isMoving && (
                  <>
                    <span className="label">→</span>
                    <span className="destination-value">{army.destination}</span>
                    {army.eta_ticks && <span className="eta">ETA: {army.eta_ticks} ticks</span>}
                  </>
                )}
              </div>

              {army.units && army.units.length > 0 && (
                <div className="unit-composition">
                  <span className="label">Units:</span>
                  <div className="units-list">
                    {army.units.map((unit, idx) => (
                      <div key={idx} className="unit-item">
                        <span className="unit-type">{unit.type}</span>
                        <span className="unit-count">×{unit.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="army-stats">
                <div className="stat-row">
                  <span className="label">Total Units:</span>
                  <span className="value">{army.unit_count}</span>
                </div>

                <div className="stat-row">
                  <span className="label">Damage/Tick:</span>
                  <span className="value">{army.damage_per_tick.toFixed(1)}</span>
                </div>

                <div className="stat-row">
                  <span className="label">Morale:</span>
                  <span className="value">{army.morale}%</span>
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
                        hpPercentageMinusNeutral >= 33.33
                          ? "#2ecc71"
                          : hpPercentageMinusNeutral >= 16.66 && hpPercentageMinusNeutral < 33.33
                          ? "#27ae60"
                          : hpPercentageMinusNeutral >= -16.66 && hpPercentageMinusNeutral < 16.66
                          ? "#f1c40f"
                          : hpPercentageMinusNeutral >= -33.33 && hpPercentageMinusNeutral < -16.66
                          ? "#e67e22"
                          : "#e74c3c"
                    }}
                  />
                </div>
              </div>

              {isSelected && (
                <div className="army-selection-indicator">
                  ★ Selected for Movement
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ArmiesList;