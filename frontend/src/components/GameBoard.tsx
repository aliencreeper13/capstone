/**
 * Game Board Component
 * Main container that displays the entire game state
 */

import React, { useState, useEffect } from "react";
import { GameState } from "../types/gameState";
import { GameApiService } from "../services/gameApi";
import EmpireStats from "./EmpireStats";
import CityStats from "./CityStats";
import BuildingsList from "./BuildingsList";
import ArmiesList from "./ArmiesList";
import "./styles/GameBoard.css";

interface Props {
  pollInterval?: number;
  useMockData?: boolean;
}

const GameBoard: React.FC<Props> = ({ pollInterval = 2000, useMockData = false }) => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

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
      } catch (err) {
        console.error("Failed to fetch game state:", err);
        setError("Failed to load game state. Using mock data...");
        // Fall back to mock data on error
        setGameState(GameApiService.getMockGameState());
      } finally {
        setLoading(false);
      }
    };

    fetchInitialState();

    // Set up polling
    const unsubscribe = GameApiService.subscribeToGameState(
      (state) => {
        setGameState(state);
        setLastUpdate(new Date());
        setError(null);
      },
      pollInterval
    );

    return unsubscribe;
  }, [pollInterval, useMockData]);

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
        {/* Left Sidebar: Empire Stats */}
        <aside className="sidebar-left">
          <EmpireStats empire={empire} currentTick={current_tick} />
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
                  <BuildingsList buildings={selected_city.buildings} />
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