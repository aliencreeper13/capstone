/**
 * Government Actions Component
 * Allows execution of government actions (tax policies, population management, etc.)
 * RESTRICTED: Only available from the capital city
 */

import React, { useState, useEffect } from "react";
import { CityData, EmpireData } from "../types/gameState";
import { GameApiService } from "../services/gameApi";
import "./styles/GovernmentActions.css";

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

  // Mock government actions (replace with actual backend data)
  const mockActions: GovernmentAction[] = [
    {
      id: "increase_tax",
      name: "Increase Tax Rate",
      description: "Increase tax collection from all cities",
      icon: "💰",
      cost_wealth: 50,
      effect: "Wealth production +20% for 50 ticks",
      category: "tax",
    },
    {
      id: "decrease_tax",
      name: "Decrease Tax Rate",
      description: "Reduce tax burden on citizens",
      icon: "💸",
      cost_wealth: 0,
      effect: "Morale +10 across all cities for 50 ticks",
      category: "tax",
    },
    {
      id: "conscription",
      name: "Conscription",
      description: "Convert eligible population to military units",
      icon: "⚔️",
      cost_wealth: 100,
      effect: "Create 50 soldiers in capital city",
      category: "population",
    },
    {
      id: "population_incentive",
      name: "Population Incentive",
      description: "Encourage population growth in capital",
      icon: "👥",
      cost_wealth: 80,
      effect: "Population growth +5% for 100 ticks",
      category: "population",
    },
    {
      id: "research_grant",
      name: "Research Grant",
      description: "Fund scientific research",
      icon: "🔬",
      cost_wealth: 150,
      effect: "Knowledge +100, unlock advanced buildings",
      category: "research",
    },
    {
      id: "diplomatic_mission",
      name: "Diplomatic Mission",
      description: "Send diplomatic envoys (future feature)",
      icon: "🕊️",
      cost_wealth: 120,
      effect: "Improve relations with other empires",
      category: "diplomacy",
    },
  ];

  useEffect(() => {
    const loadActions = async () => {
      try {
        setLoading(true);
        // For now, use mock data. Replace with actual API call when endpoint is ready
        // const data = await GameApiService.getAvailableGovernmentActions();
        setActions(mockActions);
      } catch (err) {
        console.error("Failed to load government actions:", err);
        setActions(mockActions); // Fallback to mock data
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
      setError(`Insufficient wealth! Need ${action.cost_wealth}, but only have ${city.resources.wealth.toFixed(0)}`);
      return;
    }

    try {
      setError(null);
      setSuccess(null);
      setExecuting(action.id);

      await GameApiService.executeGovernmentAction(action.id, {
        wealth_cost: action.cost_wealth,
      });

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

  const actionsByCategory = mockActions.reduce((acc, action) => {
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
            <span className="wealth-value">{city.resources.wealth.toFixed(0)} Wealth</span>
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