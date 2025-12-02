/**
 * Map Viewer Component - Phase 4
 * Interactive visualization of the world map with nodes, paths, and armies
 */

import React, { useState, useEffect, useRef } from "react";
import { GameApiService } from "../services/gameApi";
import { MapStructureData, GameNodeData } from "../types/gameState";
import "./styles/MapViewer.css";

interface Props {
  selectedArmyId?: string | null;
  onArmySelected?: (armyId: string, nodeId: string) => void;
  onMovementAttempt?: (armyId: string, destinationNodeId: string) => Promise<void>;
}

const MapViewer: React.FC<Props> = ({ selectedArmyId, onArmySelected, onMovementAttempt }) => {
  const [mapData, setMapData] = useState<MapStructureData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [adjacentNodes, setAdjacentNodes] = useState<GameNodeData[]>([]);
  const [isMoving, setIsMoving] = useState(false);
  const [moveMessage, setMoveMessage] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Fetch map structure
  useEffect(() => {
    const fetchMapData = async () => {
      try {
        setLoading(true);
        const data = await GameApiService.getMapStructure();
        setMapData(data);
        setError(null);
      } catch (err) {
        console.error("Failed to load map:", err);
        setError("Failed to load map structure");
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchMapData();

    // Poll for updates
    const interval = setInterval(fetchMapData, 2000);
    return () => clearInterval(interval);
  }, []);

  // Fetch adjacent nodes when node is selected
  useEffect(() => {
    if (!selectedNode) {
      setAdjacentNodes([]);
      return;
    }

    const fetchAdjacentNodes = async () => {
      try {
        const nodes = await GameApiService.getAdjacentNodes(selectedNode);
        setAdjacentNodes(nodes);
      } catch (err) {
        console.error("Failed to fetch adjacent nodes:", err);
        setAdjacentNodes([]);
      }
    };

    fetchAdjacentNodes();
  }, [selectedNode]);

  // Draw map
  useEffect(() => {
    if (!mapData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw paths first (so they appear behind nodes)
    ctx.strokeStyle = "#4a4a6a";
    ctx.lineWidth = 2;
    mapData.paths.forEach((path) => {
      const fromNode = mapData.nodes.find((n) => n.id === path.from_node);
      const toNode = mapData.nodes.find((n) => n.id === path.to_node);

      if (fromNode && toNode) {
        ctx.beginPath();
        ctx.moveTo(fromNode.coords[0], fromNode.coords[1]);
        ctx.lineTo(toNode.coords[0], toNode.coords[1]);
        ctx.stroke();

        // Draw army count on path if any
        if (path.armies_on_path && path.armies_on_path.length > 0) {
          const midX = (fromNode.coords[0] + toNode.coords[0]) / 2;
          const midY = (fromNode.coords[1] + toNode.coords[1]) / 2;
          ctx.fillStyle = "#ff9500";
          ctx.font = "12px Arial";
          ctx.textAlign = "center";
          ctx.fillText(`${path.armies_on_path.length} moving`, midX, midY);
        }
      }
    });

    // Draw nodes
    mapData.nodes.forEach((node) => {
      const isSelected = node.id === selectedNode;
      const isAdjacent = adjacentNodes.some((n) => n.id === node.id);
      const hasArmies = node.stationed_armies && node.stationed_armies.length > 0;

      // Node circle
      ctx.beginPath();
      ctx.arc(node.coords[0], node.coords[1], 20, 0, 2 * Math.PI);

      if (isSelected) {
        ctx.fillStyle = "#ff6b6b";
      } else if (isAdjacent && selectedNode) {
        ctx.fillStyle = "#51cf66";
      } else if (node.is_claimed) {
        ctx.fillStyle = "#4ecdc4";
      } else {
        ctx.fillStyle = "#666666";
      }
      ctx.fill();

      // Node border
      ctx.strokeStyle = hasArmies ? "#ffd700" : "#cccccc";
      ctx.lineWidth = hasArmies ? 3 : 2;
      ctx.stroke();

      // Army count badge
      if (hasArmies) {
        ctx.fillStyle = "#ffd700";
        ctx.font = "bold 12px Arial";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(`${node.stationed_armies.length}`, node.coords[0], node.coords[1]);
      }

      // City name label
      if (node.city_name) {
        ctx.fillStyle = "#ffffff";
        ctx.font = "12px Arial";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(node.city_name, node.coords[0], node.coords[1] + 30);
      }
    });

    // Draw legend
    ctx.fillStyle = "#ffffff";
    ctx.font = "12px Arial";
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText("Claimed", 10, 10);
    ctx.fillText("Unclaimed", 10, 30);
    ctx.fillText("Selected", 10, 50);
    ctx.fillText("Reachable", 10, 70);

    ctx.fillStyle = "#4ecdc4";
    ctx.fillRect(-10, 10, 8, 8);
    ctx.fillStyle = "#666666";
    ctx.fillRect(-10, 30, 8, 8);
    ctx.fillStyle = "#ff6b6b";
    ctx.fillRect(-10, 50, 8, 8);
    ctx.fillStyle = "#51cf66";
    ctx.fillRect(-10, 70, 8, 8);
  }, [mapData, selectedNode, adjacentNodes]);

  // Handle canvas click
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!mapData || !canvasRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Find clicked node
    let clickedNode: GameNodeData | null = null;
    for (const node of mapData.nodes) {
      const dx = node.coords[0] - x;
      const dy = node.coords[1] - y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      if (distance <= 20) {
        clickedNode = node;
        break;
      }
    }

    if (!clickedNode) {
      setSelectedNode(null);
      return;
    }

    // If an army is selected and we clicked an adjacent node, move it
    if (selectedArmyId && selectedNode && adjacentNodes.some((n) => n.id === clickedNode!.id)) {
      handleMoveArmy(clickedNode.id);
      return;
    }

    // Otherwise, select the node
    setSelectedNode(clickedNode.id);
    if (onArmySelected && clickedNode.stationed_armies && clickedNode.stationed_armies.length > 0) {
      onArmySelected(clickedNode.stationed_armies[0].id, clickedNode.id);
    }
  };

  // Move army to destination
  const handleMoveArmy = async (destinationNodeId: string) => {
    if (!selectedArmyId || isMoving) return;

    try {
      setIsMoving(true);
      setMoveMessage(null);

      if (onMovementAttempt) {
        await onMovementAttempt(selectedArmyId, destinationNodeId);
        setMoveMessage(`Army movement initiated!`);
        setSelectedNode(null);
      } else {
        await GameApiService.moveArmy(selectedArmyId, destinationNodeId);
        setMoveMessage(`Army movement initiated!`);
        setSelectedNode(null);
      }

      // Clear message after 3 seconds
      setTimeout(() => setMoveMessage(null), 3000);
    } catch (err) {
      console.error("Movement failed:", err);
      setMoveMessage(`Movement failed: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setIsMoving(false);
    }
  };

  if (loading) {
    // return <div className="map-viewer"><div className="loading">Loading map...</div></div>;
  }

  if (error) {
    return <div className="map-viewer"><div className="error">{error}</div></div>;
  }

  return (
    <div className="map-viewer">
      <div className="map-header">
        <h3>World Map</h3>
        {selectedNode && adjacentNodes.length > 0 && (
          <div className="adjacent-info">
            <p>Adjacent nodes: {adjacentNodes.length}</p>
            {selectedArmyId && (
              <p className="move-hint">Click an adjacent node to move army there</p>
            )}
          </div>
        )}
      </div>

      <canvas
        ref={canvasRef}
        width={800}
        height={600}
        className="map-canvas"
        onClick={handleCanvasClick}
      />

      {moveMessage && (
        <div className={`move-message ${moveMessage.includes("failed") ? "error" : "success"}`}>
          {moveMessage}
        </div>
      )}

      {selectedNode && (
        <div className="node-info">
          <h4>Selected Node: {selectedNode}</h4>
          {mapData && (
            <>
              {mapData.nodes.find((n) => n.id === selectedNode)?.stationed_armies && (
                <div className="stationed-armies">
                  <h5>Stationed Armies ({mapData.nodes.find((n) => n.id === selectedNode)?.stationed_armies.length}):</h5>
                  <ul>
                    {mapData.nodes
                      .find((n) => n.id === selectedNode)
                      ?.stationed_armies.map((army) => (
                        <li key={army.id} className={selectedArmyId === army.id ? "selected" : ""}>
                          {army.name} ({army.unit_count} units)
                        </li>
                      ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default MapViewer;