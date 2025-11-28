/**
 * World Map Visualization Component
 * Displays the world map and allows interaction with cities
 */

import React, { useState, useEffect } from "react";
import { GameApiService } from "../services/gameApi";
import "./styles/WorldMapView.css";

interface Props {
  onCitySelected?: (cityId: number) => void;
}

const WorldMapView: React.FC<Props> = ({ onCitySelected }) => {
  const [mapImageUrl, setMapImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredCity, setHoveredCity] = useState<string | null>(null);

  useEffect(() => {
    const loadMapVisualization = async () => {
      try {
        setLoading(true);
        setError(null);
        const blob = await GameApiService.getMapVisualization();
        const url = URL.createObjectURL(blob);
        setMapImageUrl(url);
      } catch (err: any) {
        setError(err.message || "Failed to load map visualization");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadMapVisualization();

    // Cleanup
    return () => {
      if (mapImageUrl) {
        URL.revokeObjectURL(mapImageUrl);
      }
    };
  }, []);

  if (loading) {
    /* return (
      <div className="world-map loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading world map...</p>
        </div>
      </div>
    ); */
  }

  if (error) {
    return (
      <div className="world-map error">
        <div className="error-message">
          <p>Failed to load map visualization</p>
          <p className="error-detail">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="world-map">
      <div className="map-header">
        <h3>World Map</h3>
        <p className="map-hint">Click on cities to select them</p>
      </div>

      {mapImageUrl && (
        <div className="map-container">
          <img
            src={mapImageUrl}
            alt="World Map"
            className="map-image"
            onError={() => setError("Failed to display map image")}
          />
        </div>
      )}

      <div className="map-footer">
        <p>🌍 Your empire spans across the known world</p>
      </div>
    </div>
  );
};

export default WorldMapView;