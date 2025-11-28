/**
 * Building Upgrades Component
 * Displays buildings with upgrade options
 */

import React, { useState, useEffect } from "react";
import { Building, Resources } from "../types/gameState";
import { GameApiService, AvailableBuilding } from "../services/gameApi";
import { newValueGivenMorale } from "../utils/game_utils";
import "./styles/BuildingUpgrades.css";

interface Props {
  buildings: Building[];
  onBuildingUpgraded: () => void;
  onBuildingCreated: () => void;
  onBuildingDemolished: () => void;
  cityResources?: Resources;
  cityMorale?: number;
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
  "woodcutter's camp": "🪚",
  "Woodcutter's Camp": "🪚",
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

interface Message {
  type: "success" | "error";
  text: string;
  id: string;
}

const BuildingUpgrades: React.FC<Props> = ({
  buildings,
  onBuildingUpgraded,
  onBuildingCreated,
  onBuildingDemolished,
  cityResources,
  cityMorale = 50,
}) => {
  const [availableBuildings, setAvailableBuildings] = useState<AvailableBuilding[]>([]);
  const [selectedBuildingType, setSelectedBuildingType] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);

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

  // Auto-remove messages after 3 seconds
  useEffect(() => {
    if (messages.length === 0) return;

    const timer = setTimeout(() => {
      setMessages((prev) => prev.slice(1));
    }, 3000);

    return () => clearTimeout(timer);
  }, [messages]);

  const addMessage = (type: "success" | "error", text: string) => {
    const id = Math.random().toString(36).substr(2, 9);
    setMessages((prev) => [...prev, { type, text, id }]);
  };

  const handleCreateBuilding = async () => {
    if (!selectedBuildingType) return;

    try {
      setError(null);
      await GameApiService.createBuilding(selectedBuildingType);
      addMessage("success", `✅ Building construction queued: ${selectedBuildingType}`);
      onBuildingCreated();
    } catch (err: any) {
      const errorMsg = err.message || "Failed to create building";
      setError(errorMsg);
      addMessage("error", `❌ ${errorMsg}`);
      console.error(err);
    }
  };

  const handleUpgradeBuilding = async (buildingId: string, buildingName: string) => {
    try {
      setError(null);
      
      const response = await GameApiService.upgradeBuilding(buildingId);
      if (response.status !== "success") {
        throw new Error(response.message || "Upgrade failed");
      }
      else{
        setUpgrading(buildingId);
        addMessage("success", `✅ Upgrade queued: ${buildingName}`);
        onBuildingUpgraded();
      }
      
    } catch (err: any) {
      const errorMsg = err.message || "Failed to upgrade building";
      setError(errorMsg);
      addMessage("error", `❌ ${errorMsg}`);
      console.error(err);
    } finally {
      setUpgrading(null);
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

  // Group buildings by name with their IDs
  const groupedBuildings = buildings.reduce(
    (acc, building) => {
      const existing = acc.find((g) => g.name === building.name);
      if (existing) {
        existing.count += 1;
        existing.buildings.push(building);
      } else {
        acc.push({
          name: building.name,
          count: 1,
          buildings: [building],
        });
      }
      return acc;
    },
    [] as Array<{
      name: string;
      count: number;
      buildings: Building[];
    }>
  );

  const buildingToCreate = availableBuildings.find((b) => b.name === selectedBuildingType);

  // Group available buildings by category
  const groupedAvailableBuildings = availableBuildings.reduce(
    (acc, building) => {
      const category = building.category || "Uncategorized";
      const existing = acc.find((g) => g.category === category);
      if (existing) {
        existing.buildings.push(building);
      } else {
        acc.push({
          category,
          buildings: [building],
        });
      }
      return acc;
    },
    [] as Array<{
      category: string;
      buildings: AvailableBuilding[];
    }>
  ).sort((a, b) => a.category.localeCompare(b.category));

  // Category icons for visual distinction
  const categoryIcons: Record<string, string> = {
    Economic: "💰",
    Civilian: "👥",
    Military: "⚔️",
    Uncategorized: "🏗️",
  };

  const getCategoryIcon = (category: string): string => {
    return categoryIcons[category] || "🏗️";
  };

  const renderBuildingEffect = (effect: any, label: string = "") => {
    const contributions: Array<{ text: string; className?: string }> = [];
    
    const resourcesAffectedByMorale = [
      { key: "food_per_tick", icon: "🌾", suffix: "/tick" },
      { key: "timber_per_tick", icon: "🪵", suffix: "/tick" },
      { key: "metal_per_tick", icon: "⚒️", suffix: "/tick" },
      { key: "wealth_per_tick", icon: "💰", suffix: "/tick" },
    ];

    for (const resource of resourcesAffectedByMorale) {
      const baselineValue = effect[resource.key];
      if (baselineValue > 0) {
        const actualValue = newValueGivenMorale(baselineValue, cityMorale);
        const difference = actualValue - baselineValue;
        const className = difference > 0 ? "morale-positive" : difference < 0 ? "morale-negative" : "";
        
        const text = `${resource.icon} ${baselineValue.toFixed(2)} → ${actualValue.toFixed(2)}${resource.suffix}`;
        contributions.push({ text, className });
      }
    }
    
    if (effect.knowledge_per_tick > 0) contributions.push({ text: `📚 ${effect.knowledge_per_tick.toFixed(2)}/tick` });
    if (effect.morale_per_tick > 0) contributions.push({ text: `😊 ${effect.morale_per_tick.toFixed(3)}/tick` });
    if (effect.food_storage > 0) contributions.push({ text: `🌾 Storage +${effect.food_storage}` });
    if (effect.timber_storage > 0) contributions.push({ text: `🌲 Storage +${effect.timber_storage}` });
    if (effect.metal_storage > 0) contributions.push({ text: `⚒️ Storage +${effect.metal_storage}` });
    if (effect.wealth_storage > 0) contributions.push({ text: `💰 Storage +${effect.wealth_storage}` });
    if (effect.population_capacity > 0) contributions.push({ text: `👥 Population +${effect.population_capacity}` });
    if (effect.defense > 0) contributions.push({ text: `🛡️ Defense +${effect.defense}` });
    if (effect.protection > 0) contributions.push({ text: `🔰 Protection +${effect.protection}` });
    if (effect.new_workers_per_tick > 0) contributions.push({ text: `👷 Workers +${effect.new_workers_per_tick.toFixed(2)}/tick` });
    if (effect.new_population_per_tick > 0) contributions.push({ text: `👶 Population +${effect.new_population_per_tick.toFixed(2)}/tick` });
    if (effect.hp_regeneration_per_tick > 0) contributions.push({ text: `❤️ HP Regen +${effect.hp_regeneration_per_tick}/tick` });
    if (effect.max_lifespan_increase > 0) contributions.push({ text: `👴 Lifespan +${effect.max_lifespan_increase}` });
    
    if (contributions.length === 0) {
      return <span className="no-effect">No benefits</span>;
    }
    
    return (
      <div className="effect-list">
        {label && <span className="effect-label">{label}</span>}
        <ul>
          {contributions.map((contrib, idx) => (
            <li key={idx} className={contrib.className}>{contrib.text}</li>
          ))}
        </ul>
      </div>
    );
  };

  // Helper to render upgrade costs with color coding
  const renderUpgradeCosts = (costs: any) => {
    if (!costs) return null;
    
    const hasFood = costs.food > 0;
    const hasTimber = costs.timber > 0;
    const hasMetal = costs.metal > 0;
    const hasWealth = costs.wealth > 0;
    
    if (!hasFood && !hasTimber && !hasMetal && !hasWealth) {
      return null;
    }
    
    const getResourceClass = (resource: string, amount: number): string => {
      if (!cityResources) return "";
      const available = cityResources[resource as keyof Resources];
      return available >= amount ? "sufficient" : "insufficient";
    };
    
    return (
      <div className="upgrade-costs">
        <span className="cost-label">💰 Upgrade Costs:</span>
        <ul className="cost-list">
          {hasFood && (
            <li className={`cost-item ${getResourceClass("food", costs.food)}`}>
              🌾 {Math.ceil(costs.food)}
            </li>
          )}
          {hasTimber && (
            <li className={`cost-item ${getResourceClass("timber", costs.timber)}`}>
              🪵 {Math.ceil(costs.timber)}
            </li>
          )}
          {hasMetal && (
            <li className={`cost-item ${getResourceClass("metal", costs.metal)}`}>
              ⚒️ {Math.ceil(costs.metal)}
            </li>
          )}
          {hasWealth && (
            <li className={`cost-item ${getResourceClass("wealth", costs.wealth)}`}>
              💰 {Math.ceil(costs.wealth)}
            </li>
          )}
        </ul>
      </div>
    );
  };

  if (loading) {
    return <div className="building-upgrades loading">Loading buildings...</div>;
  }

  return (
    <div className="building-upgrades">
      {/* Messages Container */}
      {messages.length > 0 && (
        <div className="messages-container">
          {messages.map((msg) => (
            <div key={msg.id} className={`message message-${msg.type}`}>
              {msg.text}
            </div>
          ))}
        </div>
      )}

      {error && <div className="error-message">❌ {error}</div>}

      {/* Existing Buildings Section */}
      <div className="upgrades-section">
        <h3>Your Buildings ({buildings.length})</h3>

        {buildings.length === 0 ? (
          <div className="empty-state">
            <p>No buildings yet. Create one below to get started!</p>
          </div>
        ) : (
          <div className="buildings-list">
            {groupedBuildings.map((group) => (
              <div key={group.name} className="building-group">
                <div className="group-header">
                  <span className="icon">{getBuildingIcon(group.name)}</span>
                  <span className="name">{group.name}</span>
                  <span className="count">({group.count})</span>
                </div>

                <div className="buildings-in-group">
                  {group.buildings.map((building) => (
                    <div key={building.id} className="building-item">
                      <div className="building-header-row">
                        <div className="building-details">
                          <span className="level">Level {building.level}</span>
                          <span className="space">Space: {building.space_used}</span>
                        </div>
                        <div className="building-actions">
                          <button
                            className="btn-upgrade"
                            onClick={() => handleUpgradeBuilding(building.id, group.name)}
                            disabled={upgrading === building.id}
                            title="Upgrade this building"
                          >
                            {upgrading === building.id ? "⏳ Upgrading..." : "⬆️ Upgrade"}
                          </button>
                          <button
                            className="btn-demolish"
                            onClick={() => handleDemolishBuilding(building.id)}
                            title="Demolish this building"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>

                      {/* Upgrade Costs */}
                      {renderUpgradeCosts(building.upgrade_cost)}

                      {/* Current Building Contributions */}
                      <div className="building-contributions">
                        {renderBuildingEffect(building.current_effect, "Currently providing:")}
                      </div>

                      {/* Upgrade Preview */}
                      {(building.next_level_effect.food_per_tick > building.current_effect.food_per_tick ||
                        building.next_level_effect.timber_per_tick > building.current_effect.timber_per_tick ||
                        building.next_level_effect.metal_per_tick > building.current_effect.metal_per_tick ||
                        building.next_level_effect.wealth_per_tick > building.current_effect.wealth_per_tick ||
                        building.next_level_effect.knowledge_per_tick > building.current_effect.knowledge_per_tick ||
                        building.next_level_effect.morale_per_tick > building.current_effect.morale_per_tick ||
                        building.next_level_effect.food_storage > building.current_effect.food_storage ||
                        building.next_level_effect.timber_storage > building.current_effect.timber_storage ||
                        building.next_level_effect.metal_storage > building.current_effect.metal_storage ||
                        building.next_level_effect.wealth_storage > building.current_effect.wealth_storage ||
                        building.next_level_effect.population_capacity > building.current_effect.population_capacity ||
                        building.next_level_effect.defense > building.current_effect.defense ||
                        building.next_level_effect.protection > building.current_effect.protection) && (
                        <div className="upgrade-preview">
                          <span className="preview-label">⬆️ Level {building.level + 1} (+4% bonus):</span>
                          <ul className="upgrade-changes">
                            {building.next_level_effect.food_per_tick > building.current_effect.food_per_tick && (
                              <li>🌾 {building.current_effect.food_per_tick.toFixed(2)} → {building.next_level_effect.food_per_tick.toFixed(2)}/tick</li>
                            )}
                            {building.next_level_effect.timber_per_tick > building.current_effect.timber_per_tick && (
                              <li>🌲 {building.current_effect.timber_per_tick.toFixed(2)} → {building.next_level_effect.timber_per_tick.toFixed(2)}/tick</li>
                            )}
                            {building.next_level_effect.metal_per_tick > building.current_effect.metal_per_tick && (
                              <li>⚒️ {building.current_effect.metal_per_tick.toFixed(2)} → {building.next_level_effect.metal_per_tick.toFixed(2)}/tick</li>
                            )}
                            {building.next_level_effect.wealth_per_tick > building.current_effect.wealth_per_tick && (
                              <li>💰 {building.current_effect.wealth_per_tick.toFixed(2)} → {building.next_level_effect.wealth_per_tick.toFixed(2)}/tick</li>
                            )}
                            {building.next_level_effect.knowledge_per_tick > building.current_effect.knowledge_per_tick && (
                              <li>📚 {building.current_effect.knowledge_per_tick.toFixed(2)} → {building.next_level_effect.knowledge_per_tick.toFixed(2)}/tick</li>
                            )}
                            {building.next_level_effect.morale_per_tick > building.current_effect.morale_per_tick && (
                              <li>😊 {building.current_effect.morale_per_tick.toFixed(3)} → {building.next_level_effect.morale_per_tick.toFixed(3)}/tick</li>
                            )}
                            {building.next_level_effect.food_storage > building.current_effect.food_storage && (
                              <li>🌾 Storage {building.current_effect.food_storage} → {building.next_level_effect.food_storage}</li>
                            )}
                            {building.next_level_effect.timber_storage > building.current_effect.timber_storage && (
                              <li>🪵 Storage {building.current_effect.timber_storage} → {building.next_level_effect.timber_storage}</li>
                            )}
                            {building.next_level_effect.metal_storage > building.current_effect.metal_storage && (
                              <li>⚒️ Storage {building.current_effect.metal_storage} → {building.next_level_effect.metal_storage}</li>
                            )}
                            {building.next_level_effect.wealth_storage > building.current_effect.wealth_storage && (
                              <li>💰 Storage {building.current_effect.wealth_storage} → {building.next_level_effect.wealth_storage}</li>
                            )}
                            {building.next_level_effect.population_capacity > building.current_effect.population_capacity && (
                              <li>👥 Population {building.current_effect.population_capacity} → {building.next_level_effect.population_capacity}</li>
                            )}
                            {building.next_level_effect.defense > building.current_effect.defense && (
                              <li>🛡️ Defense {building.current_effect.defense} → {building.next_level_effect.defense}</li>
                            )}
                            {building.next_level_effect.protection > building.current_effect.protection && (
                              <li>🔰 Protection {building.current_effect.protection} → {building.next_level_effect.protection}</li>
                            )}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create New Building Section */}
      <div className="create-section">
        <h3>Construct New Building</h3>

        {availableBuildings.length === 0 ? (
          <div className="empty-state">No buildings available to build</div>
        ) : (
          <>
            <div className="building-categories">
              {groupedAvailableBuildings.map((categoryGroup) => (
                <div key={categoryGroup.category} className="category-section">
                  <div className="category-header">
                    <span className="category-icon">{getCategoryIcon(categoryGroup.category)}</span>
                    <h4>{categoryGroup.category}</h4>
                  </div>
                  <div className="category-buildings">
                    {categoryGroup.buildings.map((building) => (
                      <button
                        key={building.name}
                        className={`building-option ${
                          selectedBuildingType === building.name ? "selected" : ""
                        }`}
                        onClick={() => setSelectedBuildingType(building.name)}
                        title={building.description}
                      >
                        <div className="option-name">{getBuildingIcon(building.name)} {building.name}</div>
                        <div className="option-meta">
                          Size: {building.size} | Ticks: {building.job_num_ticks}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {buildingToCreate && (
              <div className="building-preview">
                <div className="preview-info">
                  <h4>{buildingToCreate.name}</h4>
                  <p className="description">{buildingToCreate.description}</p>

                  <div className="requirements">
                    <h5>Requirements:</h5>
                    <ul>
                      {Object.entries(buildingToCreate.requirements.resources).map(
                        ([resource, amount]) => (
                          <li key={resource}>
                            {resource}: <strong>{amount}</strong>
                          </li>
                        )
                      )}
                      <li>
                        Workers: <strong>{buildingToCreate.requirements.workers}</strong>
                      </li>
                      {buildingToCreate.requirements.knowledge && (
                        <li>
                          Knowledge: <strong>{buildingToCreate.requirements.knowledge}</strong>
                        </li>
                      )}
                    </ul>
                  </div>

                  <button
                    className="btn-create"
                    onClick={handleCreateBuilding}
                  >
                    🏗️ Construct Building
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default BuildingUpgrades;