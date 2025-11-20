/**
 * Game Board Component
 * Main container that displays the entire game state
 */

import React, { useState, useEffect, useRef } from "react";
import { GameState } from "../types/gameState";
import { GameApiService } from "../services/gameApi";
import EmpireStats from "./EmpireStats";
import CityStats from "./CityStats";
import BuildingManager from "./BuildingManager";
import ArmiesList from "./ArmiesList";
import CitySwitcher from "./CitySwitcher";
import "./styles/GameBoard.css";

interface Props {
  pollInterval?: number;
  useMockData?: boolean;
}

const GameBoard: React.FC<Props> = ({ pollInterval = 1000, useMockData = false }) => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [needsRefresh, setNeedsRefresh] = useState(false);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    const fetchInitialState = async () => {
      try {
        setLoading(true);
        const state = useMockData
          ? GameApiService.getMockGameState()
          : await GameApiService.getGameState();
        setGameState(state);
        setLastUpdate(new Date());
        setError(null);
        setNeedsRefresh(false);
      } catch (err) {
        console.error("Failed to fetch game state:", err);
        setError("Failed to load game state. Check that backend is running on http://localhost:8000");
        if (!useMockData) {
          // Fall back to mock data on error
          setGameState(GameApiService.getMockGameState());
        }
      } finally {
        setLoading(false);
      }
    };

    fetchInitialState();

    // Set up polling
    unsubscribeRef.current = GameApiService.subscribeToGameState(
      (state) => {
        setGameState(state);
        setLastUpdate(new Date());
        setError(null);
        setNeedsRefresh(false);
      },
      pollInterval
    );

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, [pollInterval, useMockData]);

  // Handle building operations
  const handleBuildingCreated = () => {
    setNeedsRefresh(true);
    // Fetch immediately instead of waiting for next poll
    GameApiService.getGameState().then((state) => {
      setGameState(state);
      setLastUpdate(new Date());
      setError(null);
    }).catch(err => console.error("Failed to refresh after building creation:", err));
  };

  const handleBuildingDemolished = () => {
    setNeedsRefresh(true);
    // Fetch immediately instead of waiting for next poll
    GameApiService.getGameState().then((state) => {
      setGameState(state);
      setLastUpdate(new Date());
      setError(null);
    }).catch(err => console.error("Failed to refresh after building demolition:", err));
  };

  if (loading && !gameState) {
    return (
      <div className="game-board loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading game state...</p>
        </div>
      </div>
    );
  }

  if (!gameState) {
    return (
      <div className="game-board error">
        <div className="error-message">
          <p>Failed to load game state</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const { empire, selected_city, current_tick } = gameState;

  return (
    <div className="game-board">
      {error && (
        <div className="warning-banner">
          <span>⚠️ {error}</span>
        </div>
      )}

      <div className="board-container">
        {/* Left Sidebar: Empire Stats & City Switcher */}
        <aside className="sidebar-left">
          <div className="sidebar-section">
            <EmpireStats empire={empire} currentTick={current_tick} />
          </div>
          <div className="sidebar-section">
            <CitySwitcher onCitySelected={handleBuildingCreated} />
          </div>
        </aside>

        {/* Main Content: City View */}
        <main className="main-content">
          <div className="city-view-container">
            {/* City Stats */}
            <section className="city-stats-section">
              <CityStats city={selected_city} />
            </section>

            {/* City Contents: Buildings & Armies */}
            <section className="city-contents">
              <div className="contents-grid">
                {/* Buildings */}
                <div className="contents-panel">
                  <BuildingManager 
                    buildings={selected_city.buildings}
                    onBuildingCreated={handleBuildingCreated}
                    onBuildingDemolished={handleBuildingDemolished}
                  />
                </div>

                {/* Armies */}
                <div className="contents-panel">
                  <ArmiesList armies={selected_city.armies} />
                </div>
              </div>
            </section>
          </div>
        </main>
      </div>

      {/* Footer: Last Update */}
      <footer className="board-footer">
        <span>Last updated: {lastUpdate.toLocaleTimeString()}</span>
      </footer>
    </div>
  );
};

export default GameBoard;