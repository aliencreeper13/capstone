/**
 * Building Manager Component
 * Displays buildings and allows creating/demolishing them
 */

import React, { useState, useEffect } from "react";
import { Building } from "../types/gameState";
import { GameApiService, AvailableBuilding } from "../services/gameApi";
import "./styles/BuildingManager.css";

interface Props {
  buildings: Building[];
  onBuildingCreated: () => void;
  onBuildingDemolished: () => void;
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
  woodcutterscamp: "🪚",
  mine: "⛏️",
  granary: "🏺",
  lumberyard: "📦",
  hospital: "⚕️",
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

const BuildingManager: React.FC<Props> = ({ buildings, onBuildingCreated, onBuildingDemolished }) => {
  const [availableBuildings, setAvailableBuildings] = useState<AvailableBuilding[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedBuildingType, setSelectedBuildingType] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAvailableBuildings = async () => {
      try {
        const buildings = await GameApiService.getAvailableBuildings();
        setAvailableBuildings(buildings);
        if (buildings.length > 0) {
          setSelectedBuildingType(buildings[0].name);
        }
      } catch (err) {
        setError("Failed to load available buildings");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadAvailableBuildings();
  }, []);

  const handleCreateBuilding = async () => {
    if (!selectedBuildingType) return;

    try {
      setError(null);
      await GameApiService.createBuilding(selectedBuildingType);
      onBuildingCreated();
    } catch (err: any) {
      setError(err.message || "Failed to create building");
      console.error(err);
    }
  };

  const handleDemolishBuilding = async (buildingId: string) => {
    if (window.confirm("Are you sure you want to demolish this building?")) {
      try {
        setError(null);
        await GameApiService.demolishBuilding(buildingId);
        onBuildingDemolished();
      } catch (err: any) {
        setError(err.message || "Failed to demolish building");
        console.error(err);
      }
    }
  };

  // Group buildings by name
  const groupedBuildings = buildings.reduce(
    (acc, building) => {
      const existing = acc.find((g) => g.name === building.name);
      if (existing) {
        existing.count += 1;
        existing.levels.push(building.level);
        existing.ids.push(building.id);
      } else {
        acc.push({
          name: building.name,
          count: 1,
          levels: [building.level],
          space_total: building.space_used,
          ids: [building.id],
        });
      }
      return acc;
    },
    [] as Array<{
      name: string;
      count: number;
      levels: number[];
      space_total: number;
      ids: string[];
    }>
  );

  const buildingToCreate = availableBuildings.find((b) => b.name === selectedBuildingType);

  return (
    <div className="building-manager">
      <div className="manager-section buildings-section">
        <h3>Buildings ({buildings.length})</h3>

        {error && <div className="error-message">❌ {error}</div>}

        {buildings.length === 0 ? (
          <div className="empty-state">No buildings yet. Construct one below!</div>
        ) : (
          <div className="buildings-container">
            {groupedBuildings.map((group) => (
              <div key={group.name} className="building-group">
                <div className="building-header">
                  <span className="icon">{getBuildingIcon(group.name)}</span>
                  <div className="building-info">
                    <span className="name">{group.name}</span>
                    <span className="count">×{group.count}</span>
                  </div>
                </div>
                <div className="building-levels">
                  {group.levels.map((level, idx) => (
                    <span key={idx} className="level-badge">
                      Lv.{level}
                    </span>
                  ))}
                </div>
                <div className="building-actions">
                  {group.ids.map((id, idx) => (
                    <button
                      key={idx}
                      className="demolish-btn"
                      onClick={() => handleDemolishBuilding(id)}
                      title="Demolish this building"
                    >
                      🗑️
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="manager-section construction-section">
        <h3>Construct Building</h3>

        {loading ? (
          <div className="loading">Loading buildings...</div>
        ) : (
          <>
            <div className="building-selector">
              <select
                value={selectedBuildingType}
                onChange={(e) => setSelectedBuildingType(e.target.value)}
                disabled={isCreating}
              >
                {availableBuildings.map((b) => (
                  <option key={b.name} value={b.name}>
                    {getBuildingIcon(b.name)} {b.name}
                  </option>
                ))}
              </select>
            </div>

            {buildingToCreate && (
              <div className="building-details">
                <p className="description">{buildingToCreate.description}</p>
                
                <div className="requirements-section">
                  <h4>Construction Requirements</h4>
                  
                  <div className="requirement-item">
                    <span className="label">⏱️ Build Time:</span>
                    <span className="value">{buildingToCreate.job_num_ticks} ticks</span>
                  </div>
                  
                  <div className="requirement-item">
                    <span className="label">📏 Size:</span>
                    <span className="value">{buildingToCreate.size} space</span>
                  </div>
                  
                  {buildingToCreate.requirements.workers > 0 && (
                    <div className="requirement-item">
                      <span className="label">👷 Workers:</span>
                      <span className="value">{buildingToCreate.requirements.workers}</span>
                    </div>
                  )}
                  
                  {Object.keys(buildingToCreate.requirements.resources).length > 0 && (
                    <div className="resources-group">
                      <span className="group-label">💰 Resources Needed:</span>
                      <div className="resources-list">
                        {buildingToCreate.requirements.resources.food > 0 && (
                          <div className="resource-item">
                            <span className="resource-icon">🍞</span>
                            <span className="resource-name">Food:</span>
                            <span className="resource-value">{buildingToCreate.requirements.resources.food}</span>
                          </div>
                        )}
                        {buildingToCreate.requirements.resources.timber > 0 && (
                          <div className="resource-item">
                            <span className="resource-icon">🌲</span>
                            <span className="resource-name">Timber:</span>
                            <span className="resource-value">{buildingToCreate.requirements.resources.timber}</span>
                          </div>
                        )}
                        {buildingToCreate.requirements.resources.metal > 0 && (
                          <div className="resource-item">
                            <span className="resource-icon">⛏️</span>
                            <span className="resource-name">Metal:</span>
                            <span className="resource-value">{buildingToCreate.requirements.resources.metal}</span>
                          </div>
                        )}
                        {buildingToCreate.requirements.resources.wealth > 0 && (
                          <div className="resource-item">
                            <span className="resource-icon">💰</span>
                            <span className="resource-name">Wealth:</span>
                            <span className="resource-value">{buildingToCreate.requirements.resources.wealth}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {buildingToCreate.requirements.knowledge && buildingToCreate.requirements.knowledge > 0 && (
                    <div className="requirement-item">
                      <span className="label">📚 Knowledge:</span>
                      <span className="value">{buildingToCreate.requirements.knowledge.toFixed(1)}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            <button
              className="create-btn"
              onClick={handleCreateBuilding}
              disabled={isCreating || !selectedBuildingType}
            >
              {isCreating ? "Creating..." : "Construct"}
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default BuildingManager;