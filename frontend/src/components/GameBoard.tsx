/**
 * Game Board Component
 * Main container that displays the entire game state
 */

import React, { useState, useEffect, useRef } from "react";
import { GameState } from "../types/gameState";
import { GameApiService } from "../services/gameApi";
import EmpireStats from "./EmpireStats";
import CitySwitcher from "./CitySwitcher";
import TabContainer from "./TabContainer";
import CityOverview from "./CityOverview";
import BuildingUpgrades from "./BuildingUpgrades";
import GovernmentActions from "./GovernmentActions";
import EventFeed from "./EventFeed";
import TroopCreation from "./TroopCreation";
import ArmiesTab from "./ArmiesTab";
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
  const [, setNeedsRefresh] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  const [isTroopCreationOpen, setIsTroopCreationOpen] = useState(false);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  // Fetch events periodically
  useEffect(() => {
    const fetchEvents = async () => {
      if (useMockData) return;
      try {
        const eventsData = await GameApiService.getGameEvents(50);
        setEvents(eventsData);
      } catch (err) {
        console.error("Failed to fetch events:", err);
      }
    };

    // Fetch immediately
    fetchEvents();

    // Set up periodic polling
    const interval = setInterval(fetchEvents, pollInterval);

    return () => clearInterval(interval);
  }, [pollInterval, useMockData]);

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

  const handleUnitCreated = () => {
    setNeedsRefresh(true);
    // Fetch immediately instead of waiting for next poll
    GameApiService.getGameState().then((state) => {
      setGameState(state);
      setLastUpdate(new Date());
      setError(null);
    }).catch(err => console.error("Failed to refresh after unit creation:", err));
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
          <div className="sidebar-section">
            <button 
              className="create-units-button"
              onClick={() => setIsTroopCreationOpen(true)}
            >
              🎖️ Create Units
            </button>
          </div>
        </aside>

        {/* Main Content: Tabbed City View */}
        <main className="main-content">
          <TabContainer
            tabs={[
              {
                id: "city",
                label: "City",
                icon: "🏛️",
                content: <CityOverview city={selected_city} />,
              },
              {
                id: "armies",
                label: "Armies",
                icon: "🎖️",
                content: <ArmiesTab />,
              },
              {
                id: "buildings",
                label: "Buildings",
                icon: "🏗️",
                content: (
                  <BuildingUpgrades
                    buildings={selected_city.buildings}
                    onBuildingUpgraded={handleBuildingCreated}
                    onBuildingCreated={handleBuildingCreated}
                    onBuildingDemolished={handleBuildingDemolished}
                    cityResources={selected_city.resources}
                    cityMorale={selected_city.morale}
                  />
                ),
              },
              {
                id: "government",
                label: "Government",
                icon: "⚖️",
                content: (
                  <GovernmentActions
                    city={selected_city}
                    empire={empire}
                    onActionExecuted={handleBuildingCreated}
                  />
                ),
              },
              {
                id: "events",
                label: "Events",
                icon: "📜",
                content: <EventFeed events={events} maxVisible={50} />,
              },
            ]}
            defaultTabId="city"
          />
        </main>
      </div>

      {/* Troop Creation Modal */}
      <TroopCreation 
        isOpen={isTroopCreationOpen}
        onClose={() => setIsTroopCreationOpen(false)}
        onUnitCreated={handleUnitCreated}
      />

      {/* Footer: Last Update */}
      <footer className="board-footer">
        <span>Last updated: {lastUpdate.toLocaleTimeString()}</span>
      </footer>
    </div>
  );
};

export default GameBoard;