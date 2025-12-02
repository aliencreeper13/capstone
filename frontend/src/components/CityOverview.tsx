/**
 * City Overview Component
 * Compact display of city statistics for the main tab interface
 */

import React, { useState, useEffect } from "react";
import { CityData } from "../types/gameState";
import { GameApiService } from "../services/gameApi";
import { lerpColor } from "../utils/game_utils";
import CityArmies from "./CityArmies";
import "./styles/CityOverview.css";

interface CityOption {
  id: number;
  name: string;
  coords: [number, number];
}

interface Props {
  city: CityData;
}

const CityOverview: React.FC<Props> = ({ city }) => {
  const [expandLoading, setExpandLoading] = useState(false);
  const [expandMessage, setExpandMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [transferLoading, setTransferLoading] = useState(false);
  const [transferMessage, setTransferMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [showTransferPanel, setShowTransferPanel] = useState(false);
  const [targetCityId, setTargetCityId] = useState<number | null>(null);
  const [transferResources, setTransferResources] = useState({
    food: 0,
    timber: 0,
    metal: 0,
    wealth: 0,
  });
  const [citiesList, setCitiesList] = useState<CityOption[]>([]);

  useEffect(() => {
    const fetchCities = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/cities/list");
        if (response.ok) {
          const data = await response.json();
          setCitiesList(data.cities || []);
        }
      } catch (error) {
        console.error("Failed to fetch cities list:", error);
      }
    };

    fetchCities();
  }, []);

  const expansionCost = 500;
  const canExpand = city.resources.wealth >= expansionCost && city.space_total < city.max_space;
  const isMaxed = city.space_total >= city.max_space;

  const handleExpandCity = async () => {
    setExpandLoading(true);
    setExpandMessage(null);
    try {
      const response = await GameApiService.expandCity(1);
      if (response.status === "success") {
        setExpandMessage({ type: "success", text: "✅ City expanded!" });
      } else {
        setExpandMessage({ type: "error", text: `❌ ${response.message}` });
      }
    } catch (error: any) {
      setExpandMessage({ type: "error", text: `❌ ${error.message || "Failed to expand city"}` });
    } finally {
      setExpandLoading(false);
    }
  };

  const calculateTransferCost = (targetCityId: number | null): { wealthCost: number; transferTicks: number } => {
    if (targetCityId === null) {
      return { wealthCost: 0, transferTicks: 0 };
    }

    const targetCity = citiesList.find((c) => c.id === targetCityId);
    if (!targetCity) {
      return { wealthCost: 0, transferTicks: 0 };
    }

    const dx = Math.abs(city.coords[0] - targetCity.coords[0]);
    const dy = Math.abs(city.coords[1] - targetCity.coords[1]);
    const distance = Math.max(dx, dy);

    const wealthCost = distance * 0.1;
    const transferTicks = Math.max(1, Math.floor(distance * 1));

    return { wealthCost, transferTicks };
  };

  const handleTransfer = async () => {
    if (targetCityId === null) {
      setTransferMessage({ type: "error", text: "❌ Please select a destination city" });
      return;
    }

    const totalResourcesToTransfer =
      transferResources.food +
      transferResources.timber +
      transferResources.metal +
      transferResources.wealth;

    if (totalResourcesToTransfer === 0) {
      setTransferMessage({ type: "error", text: "❌ Please select at least one resource to transfer" });
      return;
    }

    setTransferLoading(true);
    setTransferMessage(null);
    try {
      const response = await GameApiService.transferResources(
        targetCityId,
        transferResources.food,
        transferResources.timber,
        transferResources.metal,
        transferResources.wealth
      );

      if (response.status === "success") {
        setTransferMessage({ type: "success", text: `✅ ${response.message}` });
        setTransferResources({ food: 0, timber: 0, metal: 0, wealth: 0 });
        setTargetCityId(null);
        setShowTransferPanel(false);
      } else {
        setTransferMessage({ type: "error", text: `❌ ${response.message}` });
      }
    } catch (error: any) {
      setTransferMessage({ type: "error", text: `❌ ${error.message || "Failed to transfer resources"}` });
    } finally {
      setTransferLoading(false);
    }
  };

  const handleTransferResourceChange = (resource: keyof typeof transferResources, value: number) => {
    setTransferResources((prev) => ({
      ...prev,
      [resource]: Math.max(0, value),
    }));
  };

  const moraleMinusNeutral = city.morale - 50;
  const moraleStatus =
    moraleMinusNeutral >= 33.33
      ? "Outstanding"
      : moraleMinusNeutral >= 16.66 && moraleMinusNeutral < 33.33
      ? "Excellent"
      : moraleMinusNeutral >= -16.66 && moraleMinusNeutral < 16.66
      ? "Neutral"
      : moraleMinusNeutral >= -33.33 && moraleMinusNeutral < -16.66
      ? "Poor"
      : "Critical";

  const getMoraleColor = () => {
    const clamped = Math.max(-50, Math.min(50, moraleMinusNeutral));

    if (clamped < 0) {
      const t = (clamped + 50) / 50;
      return lerpColor("#e74c3c", "#f1c40f", t);
    } else {
      const t = clamped / 50;
      return lerpColor("#f1c40f", "#2ecc71", t);
    }
  };

  const hpPercentage = (city.hitpoints / city.max_hitpoints) * 100;
  const defenseLevel = city.defense > 500 ? "Fortified" : city.defense > 200 ? "Protected" : "Vulnerable";

  return (
    <div className="city-overview">
      {/* City Header */}
      <div className="overview-header">
        <h2>{city.name}</h2>
        <span className="city-coords">
          📍 ({city.coords[0]}, {city.coords[1]})
        </span>
      </div>

      {/* Quick Stats Grid */}
      <div className="quick-stats-grid">
        {/* Population */}
        <div className="stat-box">
          <div className="stat-label">👥 Population</div>
          <div className="stat-value">{city.population.total}</div>
          <div className="stat-subtext">{city.population.employed}/{city.population.employable} employed</div>
        </div>

        {/* Morale */}
        <div className="stat-box">
          <div className="stat-label">😊 Morale</div>
          <div className="morale-bar-small">
            <div
              className="morale-fill"
              style={{
                width: `${city.morale}%`,
                backgroundColor: getMoraleColor(),
              }}
            />
          </div>
          <div className="stat-value">{city.morale.toFixed(1)}%</div>
          <div className="stat-subtext">{moraleStatus}</div>
        </div>

        {/* Defense */}
        <div className="stat-box">
          <div className="stat-label">🛡️ Defense</div>
          <div className="stat-value">{city.defense.toFixed(0)}</div>
          <div className="stat-subtext">{defenseLevel}</div>
        </div>

        {/* Protection */}
        <div className="stat-box">
          <div className="stat-label">🔰 Protection</div>
          <div className="stat-value">{city.protection.toFixed(0)}</div>
          <div className="stat-subtext">{defenseLevel}</div>
        </div>

        {/* Health */}
        <div className="stat-box">
          <div className="stat-label">❤️ Health</div>
          <div className="hp-bar-small">
            <div
              className="hp-fill"
              style={{
                width: `${hpPercentage}%`,
                backgroundColor: hpPercentage > 50 ? "#27ae60" : "#e74c3c",
              }}
            />
          </div>
          <div className="stat-value">
            {city.hitpoints.toFixed(0)}/{city.max_hitpoints}
          </div>
        </div>

        {/* Space */}
        <div className="stat-box">
          <div className="stat-label">📦 Space</div>
          <div className="space-bar-small">
            <div
              className="space-fill"
              style={{
                width: `${(city.space_used / city.space_total) * 100}%`,
              }}
            />
          </div>
          <div className="stat-value">
            {city.space_used}/{city.space_total}
          </div>
        </div>

        {/* Buildings Count */}
        <div className="stat-box">
          <div className="stat-label">🏗️ Buildings</div>
          <div className="stat-value">{city.buildings.length}</div>
          <div className="stat-subtext">structures</div>
        </div>
      </div>

      {/* Resources Overview */}
      <div className="resources-overview">
        <h3>Resources</h3>
        <div className="resource-cards">
          {[
            { name: "Food", icon: "🍞", value: city.resources.food, capacity: city.resource_capacities.food },
            { name: "Timber", icon: "🌲", value: city.resources.timber, capacity: city.resource_capacities.timber },
            { name: "Metal", icon: "⛏️", value: city.resources.metal, capacity: city.resource_capacities.metal },
            { name: "Wealth", icon: "💰", value: city.resources.wealth, capacity: city.resource_capacities.wealth },
          ].map((resource) => {
            const percentage = (resource.value / resource.capacity) * 100;
            return (
              <div key={resource.name} className="resource-card">
                <div className="resource-header">
                  <span className="resource-icon">{resource.icon}</span>
                  <span className="resource-name">{resource.name}</span>
                </div>
                <div className="resource-value">
                  {Math.floor(resource.value)} / {resource.capacity}
                </div>
                <div className="resource-bar">
                  <div
                    className="resource-fill"
                    style={{
                      width: `${Math.min(percentage, 100)}%`,
                      backgroundColor: percentage > 80 ? "#27ae60" : percentage > 50 ? "#f39c12" : "#e74c3c",
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* City Expansion Section */}
      <div className="expansion-section">
        <h3>Expand Region</h3>
        
        {expandMessage && (
          <div className={`expansion-message expansion-message-${expandMessage.type}`}>
            {expandMessage.text}
          </div>
        )}

        <div className="expansion-info">
          <div className="expansion-cost">
            <span className="expansion-cost-label">Cost per expansion:</span>
            <span className={`expansion-cost-value ${canExpand || isMaxed ? "sufficient" : "insufficient"}`}>
              💰 {expansionCost}
            </span>
          </div>

          <div className="expansion-capacity">
            <span className="expansion-capacity-label">Region capacity:</span>
            <span className="expansion-capacity-value">
              {city.space_total} / {city.max_space}
            </span>
          </div>

          {isMaxed ? (
            <div className="expansion-status maxed">
              ✓ Region is at maximum capacity
            </div>
          ) : (
            <button
              className={`btn-expand ${canExpand ? "enabled" : "disabled"}`}
              onClick={handleExpandCity}
              disabled={!canExpand || expandLoading}
              title={
                !canExpand
                  ? city.resources.wealth < expansionCost
                    ? `Need ${expansionCost} wealth`
                    : "Region is at capacity"
                  : "Expand region"
              }
            >
              {expandLoading ? "⏳ Expanding..." : "🏗️ Expand Region"}
            </button>
          )}
        </div>
      </div>

      {/* Resource Transfer Section */}
      <div className="transfer-section">
        <h3>Transfer Resources</h3>
        
        {transferMessage && (
          <div className={`transfer-message transfer-message-${transferMessage.type}`}>
            {transferMessage.text}
          </div>
        )}

        {!showTransferPanel ? (
          <button 
            className="btn-transfer-open"
            onClick={() => setShowTransferPanel(true)}
          >
            📤 Transfer to Another City
          </button>
        ) : (
          <div className="transfer-panel">
            <div className="transfer-header">
              <h4>Transfer Resources</h4>
              <button 
                className="btn-transfer-close"
                onClick={() => setShowTransferPanel(false)}
              >
                ✕
              </button>
            </div>

            <div className="transfer-destination">
              <label>Destination City:</label>
              <select 
                value={targetCityId ?? ""}
                onChange={(e) => setTargetCityId(e.target.value ? parseInt(e.target.value) : null)}
              >
                <option value="">Select a city...</option>
                {citiesList.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.coords[0]}, {c.coords[1]})
                  </option>
                ))}
              </select>
            </div>

            <div className="transfer-resources-inputs">
              <div className="transfer-resource-input">
                <label>🍞 Food:</label>
                <input 
                  type="number" 
                  value={transferResources.food}
                  onChange={(e) => handleTransferResourceChange("food", parseFloat(e.target.value) || 0)}
                  max={city.resources.food}
                  min={0}
                />
                <span className="max-available">/{city.resources.food.toFixed(0)}</span>
              </div>

              <div className="transfer-resource-input">
                <label>🌲 Timber:</label>
                <input 
                  type="number" 
                  value={transferResources.timber}
                  onChange={(e) => handleTransferResourceChange("timber", parseFloat(e.target.value) || 0)}
                  max={city.resources.timber}
                  min={0}
                />
                <span className="max-available">/{city.resources.timber.toFixed(0)}</span>
              </div>

              <div className="transfer-resource-input">
                <label>⛏️ Metal:</label>
                <input 
                  type="number" 
                  value={transferResources.metal}
                  onChange={(e) => handleTransferResourceChange("metal", parseFloat(e.target.value) || 0)}
                  max={city.resources.metal}
                  min={0}
                />
                <span className="max-available">/{city.resources.metal.toFixed(0)}</span>
              </div>

              <div className="transfer-resource-input">
                <label>💰 Wealth:</label>
                <input 
                  type="number" 
                  value={transferResources.wealth}
                  onChange={(e) => handleTransferResourceChange("wealth", parseFloat(e.target.value) || 0)}
                  max={city.resources.wealth}
                  min={0}
                />
                <span className="max-available">/{city.resources.wealth.toFixed(0)}</span>
              </div>
            </div>

            {targetCityId !== null && (
              <div className="transfer-cost-info">
                <div className="cost-detail">
                  <span>Wealth Cost:</span>
                  <span className="cost-value">💰 {calculateTransferCost(targetCityId).wealthCost.toFixed(1)}</span>
                </div>
                <div className="cost-detail">
                  <span>Transfer Duration:</span>
                  <span className="cost-value">⏱️ {calculateTransferCost(targetCityId).transferTicks} ticks</span>
                </div>
              </div>
            )}

            <button 
              className={`btn-transfer-confirm ${targetCityId !== null ? "enabled" : "disabled"}`}
              onClick={handleTransfer}
              disabled={targetCityId === null || transferLoading}
            >
              {transferLoading ? "⏳ Transferring..." : "✓ Confirm Transfer"}
            </button>
          </div>
        )}
      </div>

      {/* City Armies Section */}
      <CityArmies armies={city.armies} cityName={city.name} />
    </div>
  );
};

export default CityOverview;