/**
 * Armies Tab Component - Phase 4
 * Main interface for army management and movement
 * Integrates MapViewer and ArmiesList
 */

import React, { useState, useEffect } from "react";
import { GameApiService } from "../services/gameApi";
import { Army } from "../types/gameState";
import MapViewer from "./MapViewer";
import ArmiesList from "./ArmiesList";
import "./styles/ArmiesTab.css";

const ArmiesTab: React.FC = () => {
  const [armies, setArmies] = useState<Army[]>([]);
  const [selectedArmyId, setSelectedArmyId] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [movementStatus, setMovementStatus] = useState<string | null>(null);

  // Fetch armies
  useEffect(() => {
    const fetchArmies = async () => {
      try {
        setLoading(true);
        const data = await GameApiService.getArmies();
        setArmies(data);
        setError(null);
      } catch (err) {
        console.error("Failed to load armies:", err);
        setError("Failed to load armies");
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchArmies();

    // Poll for updates
    const interval = setInterval(fetchArmies, 2000);
    return () => clearInterval(interval);
  }, []);

  // Handle army selection
  const handleArmySelect = (armyId: string) => {
    if (selectedArmyId === armyId) {
      setSelectedArmyId(null);
      setSelectedNodeId(null);
    } else {
      setSelectedArmyId(armyId);
      // Find the army's current node
      const army = armies.find((a) => a.id === armyId);
      if (army) {
        const nodeId = `node_${army.location.split(" ").join("_")}`;
        setSelectedNodeId(nodeId);
      }
    }
  };

  // Handle movement attempt
  const handleMovementAttempt = async (armyId: string, destinationNodeId: string) => {
    try {
      setMovementStatus(null);
      await GameApiService.moveArmy(armyId, destinationNodeId);
      setMovementStatus(`Army movement initiated to ${destinationNodeId}`);
      setSelectedArmyId(null);
      setSelectedNodeId(null);

      // Clear message after 3 seconds
      setTimeout(() => setMovementStatus(null), 3000);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Unknown error";
      setMovementStatus(`Movement failed: ${errorMsg}`);
    }
  };

  if (loading) {
    /* return (
      <div className="armies-tab">
        <div className="loading-message">Loading armies...</div>
      </div>
    ); */
  }

  return (
    <div className="armies-tab">
      {error && <div className="error-message">{error}</div>}

      {movementStatus && (
        <div className={`status-message ${movementStatus.includes("failed") ? "error" : "success"}`}>
          {movementStatus}
        </div>
      )}

      <div className="armies-tab-container">
        <div className="map-section">
          <MapViewer
            selectedArmyId={selectedArmyId}
            onArmySelected={(armyId, nodeId) => {
              setSelectedArmyId(armyId);
              setSelectedNodeId(nodeId);
            }}
            onMovementAttempt={handleMovementAttempt}
          />
        </div>

        <div className="armies-section">
          <ArmiesList
            armies={armies}
            selectedArmyId={selectedArmyId}
            onArmySelect={handleArmySelect}
          />
        </div>
      </div>

      <div className="armies-info">
        <div className="info-item">
          <span className="info-label">Total Armies:</span>
          <span className="info-value">{armies.length}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Moving:</span>
          <span className="info-value">{armies.filter((a) => a.destination).length}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Stationary:</span>
          <span className="info-value">{armies.filter((a) => !a.destination).length}</span>
        </div>
        {selectedArmyId && (
          <div className="info-item highlighted">
            <span className="info-label">Selected:</span>
            <span className="info-value">{armies.find((a) => a.id === selectedArmyId)?.name || "Unknown"}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ArmiesTab;