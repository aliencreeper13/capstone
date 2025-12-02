/**
 * Armies Tab Component
 * Main interface for army management and movement on the world map
 */

import React from "react";
import WorldMapViewer from "./WorldMapViewer";
import "./styles/ArmiesTab.css";

const ArmiesTab: React.FC = () => {
  return (
    <div className="armies-tab">
      <WorldMapViewer />
    </div>
  );
};

export default ArmiesTab;
