import React, { useState } from "react";
import { Army, GameNodeData } from "../types/gameState";
import { GameApiService } from "../services/gameApi";
import "./styles/ArmyDetailPanel.css";

interface Props {
  army: Army | null;
  adjacentNodes: GameNodeData[];
  onMovement?: (status: string) => void;
  onClose?: () => void;
}

const ArmyDetailPanel: React.FC<Props> = ({ army, adjacentNodes, onMovement, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  if (!army) return null;

  const hpPercentage = army.max_hp > 0 ? (army.current_hp / army.max_hp) * 100 : 0;

  const handleMove = async (destNodeId: string) => {
    setLoading(true);
    try {
      await GameApiService.moveArmy(army.id, destNodeId);
      setMessage({ type: "success", text: "✓ Army moving" });
      onMovement?.(`Army moving`);
    } catch (error: any) {
      setMessage({ type: "error", text: `✗ ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleHalt = async () => {
    setLoading(true);
    try {
      await GameApiService.haltArmy(army.id);
      setMessage({ type: "success", text: "✓ Army halted" });
      onMovement?.("Halted");
    } catch (error: any) {
      setMessage({ type: "error", text: `✗ ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleResume = async () => {
    setLoading(true);
    try {
      await GameApiService.resumeArmy(army.id);
      setMessage({ type: "success", text: "✓ Resumed" });
      onMovement?.("Resumed");
    } catch (error: any) {
      setMessage({ type: "error", text: `✗ ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleReverse = async () => {
    setLoading(true);
    try {
      await GameApiService.reverseArmy(army.id);
      setMessage({ type: "success", text: "✓ Reversed" });
      onMovement?.("Reversed");
    } catch (error: any) {
      setMessage({ type: "error", text: `✗ ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="army-detail-panel">
      <div className="panel-header">
        <h3>{army.name}</h3>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>
      {message && <div className={`msg ${message.type}`}>{message.text}</div>}
      <div className="panel-content">
        <div className="info-grid">
          <div className="row"><span>Location:</span><span>{army.location}</span></div>
          <div className="row"><span>Units:</span><span>{army.unit_count}</span></div>
          <div className="row"><span>Speed:</span><span>{army.speed.toFixed(1)}</span></div>
          <div className="row"><span>Morale:</span><span>{army.morale.toFixed(0)}%</span></div>
        </div>
        <div className="hp-section">
          <div className="hp-bar">
            <div className="hp-fill" style={{width: `${hpPercentage}%`}} />
          </div>
          <span>{army.current_hp.toFixed(0)} / {army.max_hp}</span>
        </div>
        {!army.is_on_path ? (
          <div className="moves">
            {adjacentNodes.map((n) => (
              <button key={n.id} onClick={() => handleMove(n.id)} disabled={loading}>
                {n.city_name || `(${n.coords[0]}, ${n.coords[1]})`}
              </button>
            ))}
          </div>
        ) : (
          <div className="controls">
            {army.is_halted ? (
              <button onClick={handleResume} disabled={loading}>▶ Resume</button>
            ) : (
              <button onClick={handleHalt} disabled={loading}>⏸ Halt</button>
            )}
            <button onClick={handleReverse} disabled={loading}>↩ Reverse</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ArmyDetailPanel;
