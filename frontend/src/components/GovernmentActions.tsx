/**
 * Government Actions Component
 * Allows execution of government actions (tax policies, population management, etc.)
 * RESTRICTED: Only available from the capital city
 */

import React, { useState, useEffect } from "react";
import { CityData, EmpireData } from "../types/gameState";
import { GameApiService } from "../services/gameApi";
import "./styles/GovernmentActions.css";
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
interface Props {
  city: CityData;
  empire: EmpireData;
  onActionExecuted: () => void;
}

interface GovernmentAction {
  id: string;
  name: string;
  description: string;
  icon: string;
  cost_wealth: number;
  effect: string;
  category: "tax" | "population" | "research" | "diplomacy";
}

const GovernmentActions: React.FC<Props> = ({ city, empire, onActionExecuted }) => {
  const [actions, setActions] = useState<GovernmentAction[]>([]);
  const [executing, setExecuting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const isCapitalCity = city.name === empire.capital_name;

  useEffect(() => {
    const loadActions = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/government/available-actions`);
        if (!response.ok) {
          throw new Error(`Failed to fetch: ${response.statusText}`);
        }
        const data = await response.json();
        setActions(data.actions || []);
      } catch (err) {
        console.error("Failed to load government actions:", err);
        setActions([]); // Empty list on error instead of mock data
      } finally {
        setLoading(false);
      }
    };

    loadActions();
  }, []);

  const handleExecuteAction = async (action: GovernmentAction) => {
    if (!isCapitalCity) {
      setError("Government actions can only be executed from the capital city!");
      return;
    }

    // Check if capital has enough wealth
    if (city.resources.wealth < action.cost_wealth) {
      setError(`Insufficient wealth! Need ${action.cost_wealth}, but only have ${Math.floor(city.resources.wealth)}`);
      return;
    }

    try {
      setError(null);
      setSuccess(null);
      setExecuting(action.id);

      await GameApiService.executeGovernmentAction(action.id);

      setSuccess(`✓ ${action.name} executed successfully!`);
      onActionExecuted();
      setExecuting(null);

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || `Failed to execute ${action.name}`);
      console.error(err);
      setExecuting(null);
    }
  };

  const actionsByCategory = actions.reduce((acc, action) => {
    if (!acc[action.category]) {
      acc[action.category] = [];
    }
    acc[action.category].push(action);
    return acc;
  }, {} as Record<string, GovernmentAction[]>);

  const categoryIcons: Record<string, string> = {
    tax: "💰",
    population: "👥",
    research: "🔬",
    diplomacy: "🕊️",
  };

  const categoryNames: Record<string, string> = {
    tax: "Tax Policies",
    population: "Population Management",
    research: "Research & Development",
    diplomacy: "Diplomacy",
  };

  if (loading) {
    return <div className="government-actions loading">Loading government actions...</div>;
  }

  return (
    <div className="government-actions">
      {!isCapitalCity && (
        <div className="capital-only-notice">
          <span className="notice-icon">🏛️</span>
          <p>Government actions can only be executed from <strong>{empire.capital_name}</strong> (the capital city)</p>
          <p>Current city: <strong>{city.name}</strong></p>
        </div>
      )}

      {error && <div className="error-message">❌ {error}</div>}
      {success && <div className="success-message">✅ {success}</div>}

      <div className="actions-header">
        <h3>Government Actions</h3>
        <div className="treasury-info">
          <span className="wealth-display">
            <span className="wealth-icon">💰</span>
            <span className="wealth-value">{Math.floor(city.resources.wealth)} Wealth</span>
          </span>
        </div>
      </div>

      {Object.entries(actionsByCategory).map(([category, categoryActions]) => (
        <div key={category} className="action-category">
          <div className="category-header">
            <span className="category-icon">{categoryIcons[category]}</span>
            <h4>{categoryNames[category]}</h4>
          </div>

          <div className="actions-list">
            {categoryActions.map((action) => {
              const canAfford = city.resources.wealth >= action.cost_wealth;
              const isDisabled = !isCapitalCity || !canAfford || executing === action.id;

              return (
                <div
                  key={action.id}
                  className={`action-card ${isDisabled ? "disabled" : ""} ${
                    executing === action.id ? "executing" : ""
                  }`}
                >
                  <div className="action-header">
                    <span className="action-icon">{action.icon}</span>
                    <div className="action-info">
                      <h5>{action.name}</h5>
                      <p className="description">{action.description}</p>
                    </div>
                  </div>

                  <div className="action-details">
                    <div className="effect-box">
                      <span className="effect-label">Effect:</span>
                      <span className="effect-text">{action.effect}</span>
                    </div>

                    <div className="cost-box">
                      <span className="cost-label">Cost:</span>
                      <span className={`cost-value ${!canAfford ? "insufficient" : ""}`}>
                        💰 {action.cost_wealth}
                      </span>
                    </div>
                  </div>

                  <button
                    className="btn-execute"
                    onClick={() => handleExecuteAction(action)}
                    disabled={isDisabled}
                    title={
                      !isCapitalCity
                        ? "Only available from capital"
                        : !canAfford
                        ? "Insufficient wealth"
                        : "Execute this action"
                    }
                  >
                    {executing === action.id ? "⏳ Executing..." : "Execute"}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      ))}

      <div className="actions-footer">
        <p>
          <span className="info-icon">ℹ️</span>
          Government actions shape your empire's future. Choose wisely!
        </p>
      </div>
    </div>
  );
};

export default GovernmentActions;