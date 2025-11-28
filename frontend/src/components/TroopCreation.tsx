/**
 * Troop Creation Modal Component
 * Displays available mobile units (troops and passive units) for creation
 * Shows building requirements and allows user to create units
 */

import React, { useState, useEffect } from "react";
import { GameApiService } from "../services/gameApi";
import "./styles/TroopCreation.css";

interface BuildingRequirement {
  building_name: string;
  minimum_level: number;
  current_level: number;
  is_present: boolean;
}

interface MobileUnit {
  unit_type: string;
  name: string;
  description: string;
  size: number;
  job_ticks: number;
  is_troop: boolean;
  creation_cost: {
    food: number;
    timber: number;
    metal: number;
    wealth: number;
  };
  building_requirements: BuildingRequirement[];
  can_create: boolean;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onUnitCreated?: () => void;
}

const TroopCreation: React.FC<Props> = ({ isOpen, onClose, onUnitCreated }) => {
  const [troops, setTroops] = useState<MobileUnit[]>([]);
  const [passiveUnits, setPassiveUnits] = useState<MobileUnit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creatingUnit, setCreatingUnit] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchAvailableMobileUnits();
    }
  }, [isOpen]);

  const fetchAvailableMobileUnits = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await GameApiService.getAvailableMobileUnits();
      setTroops(data.troops || []);
      setPassiveUnits(data.passive_units || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load units");
      console.error("Error fetching mobile units:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUnit = async (unitType: string) => {
    setCreatingUnit(unitType);
    try {
      await GameApiService.createMobileUnit(unitType);
      onUnitCreated?.();
      // Refresh the list
      await fetchAvailableMobileUnits();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create unit");
    } finally {
      setCreatingUnit(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="troop-creation-overlay" onClick={onClose}>
      <div className="troop-creation-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Create Mobile Units</h2>
          <button className="close-button" onClick={onClose}>
            ✕
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}
        {loading && <div className="loading">Loading available units...</div>}

        {!loading && (
          <div className="modal-content">
            {/* Troops Section */}
            {troops.length > 0 && (
              <div className="units-section">
                <h3 className="section-title">Troops</h3>
                <div className="units-grid">
                  {troops.map((unit) => (
                    <UnitCard
                      key={unit.unit_type}
                      unit={unit}
                      onCreate={() => handleCreateUnit(unit.unit_type)}
                      isCreating={creatingUnit === unit.unit_type}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Passive Units Section */}
            {passiveUnits.length > 0 && (
              <div className="units-section">
                <h3 className="section-title">Passive Units</h3>
                <div className="units-grid">
                  {passiveUnits.map((unit) => (
                    <UnitCard
                      key={unit.unit_type}
                      unit={unit}
                      onCreate={() => handleCreateUnit(unit.unit_type)}
                      isCreating={creatingUnit === unit.unit_type}
                    />
                  ))}
                </div>
              </div>
            )}

            {troops.length === 0 && passiveUnits.length === 0 && !loading && (
              <div className="no-units">
                <p>No mobile units available for creation.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

interface UnitCardProps {
  unit: MobileUnit;
  onCreate: () => void;
  isCreating: boolean;
}

const UnitCard: React.FC<UnitCardProps> = ({ unit, onCreate, isCreating }) => {
  const canCreate = unit.can_create;

  return (
    <div className={`unit-card ${!canCreate ? "disabled" : ""}`}>
      <div className="unit-header">
        <h4>{unit.name}</h4>
        <span className="unit-size">Size: {unit.size}</span>
      </div>

      <p className="unit-description">{unit.description}</p>

      <div className="unit-info">
        <div className="info-row">
          <span className="label">Construction Time:</span>
          <span className="value">{unit.job_ticks} ticks</span>
        </div>
      </div>

      {/* Creation Cost */}
      <div className="creation-cost">
        <h5>Cost</h5>
        <div className="cost-items">
          {unit.creation_cost.food > 0 && (
            <div className="cost-item">
              <span>🌾 Food:</span>
              <span>{Math.round(unit.creation_cost.food)}</span>
            </div>
          )}
          {unit.creation_cost.timber > 0 && (
            <div className="cost-item">
              <span>🌲 Timber:</span>
              <span>{Math.round(unit.creation_cost.timber)}</span>
            </div>
          )}
          {unit.creation_cost.metal > 0 && (
            <div className="cost-item">
              <span>⚙️ Metal:</span>
              <span>{Math.round(unit.creation_cost.metal)}</span>
            </div>
          )}
          {unit.creation_cost.wealth > 0 && (
            <div className="cost-item">
              <span>💰 Wealth:</span>
              <span>{Math.round(unit.creation_cost.wealth)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Building Requirements */}
      {unit.building_requirements.length > 0 && (
        <div className="building-requirements">
          <h5>Building Requirements</h5>
          {unit.building_requirements.map((req) => (
            <div key={req.building_name} className="requirement-item">
              <div className="requirement-name">
                {req.building_name}
                <span
                  className={`requirement-status ${
                    req.is_present ? "present" : "missing"
                  }`}
                >
                  {req.is_present ? "✓" : "✗"}
                </span>
              </div>
              <div className="requirement-level">
                <span className="label">Level Required:</span>
                <span className="value">
                  {req.minimum_level}
                  {req.is_present && (
                    <span className="current-level"> (Current: {req.current_level})</span>
                  )}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Button */}
      <button
        className={`create-button ${!canCreate ? "disabled" : ""}`}
        onClick={onCreate}
        disabled={!canCreate || isCreating}
      >
        {isCreating ? "Creating..." : "Create"}
      </button>

      {!canCreate && unit.building_requirements.length > 0 && (
        <div className="requirement-warning">
          ⚠️ Required buildings not available
        </div>
      )}
    </div>
  );
};

export default TroopCreation;