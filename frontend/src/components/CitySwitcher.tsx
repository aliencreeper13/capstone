/**
 * City Switcher Component
 * Displays list of all cities and allows switching between them
 */

import React, { useState, useEffect } from "react";
import "./styles/CitySwitcher.css";

interface City {
  id: number;
  name: string;
  coords: [number, number];
  population: number;
  is_selected: boolean;
  resources: {
    food: number;
    timber: number;
    metal: number;
    wealth: number;
  };
  buildings_count: number;
}

interface Props {
  onCitySelected: () => void;
}

const CitySwitcher: React.FC<Props> = ({ onCitySelected }) => {
  const [cities, setCities] = useState<City[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCities = async () => {
      try {
        setLoading(true);
        const response = await fetch("http://localhost:8000/api/cities/list");
        if (!response.ok) throw new Error("Failed to fetch cities");
        const data = await response.json();
        setCities(data.cities);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch cities:", err);
        setError("Failed to load cities");
      } finally {
        setLoading(false);
      }
    };

    fetchCities();

    // Refresh cities every 2 seconds
    const interval = setInterval(fetchCities, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectCity = async (cityId: number) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/cities/select/${cityId}`,
        { method: "POST" }
      );
      if (!response.ok) throw new Error("Failed to select city");
      setCities(
        cities.map((c) => ({
          ...c,
          is_selected: c.id === cityId,
        }))
      );
      onCitySelected();
    } catch (err) {
      console.error("Failed to select city:", err);
      setError("Failed to select city");
    }
  };

  if (loading) {
    // return <div className="city-switcher loading">Loading cities...</div>;
  }

  return (
    <div className="city-switcher">
      <div className="city-switcher-header">
        <h3>🏛️ Cities ({cities.length})</h3>
      </div>

      {error && <div className="city-switcher-error">{error}</div>}

      <div className="cities-list">
        {cities.map((city) => (
          <div
            key={city.id}
            className={`city-item ${city.is_selected ? "selected" : ""}`}
            onClick={() => handleSelectCity(city.id)}
          >
            <div className="city-item-header">
              <div className="city-name">{city.name}</div>
              {city.is_selected && <div className="city-indicator">✓</div>}
            </div>

            <div className="city-info">
              <div className="city-coords">
                📍 ({city.coords[0]}, {city.coords[1]})
              </div>
              <div className="city-population">👥 {city.population}</div>
            </div>

            <div className="city-stats">
              <div className="stat-row">
                <span className="stat-label">🌾</span>
                <span className="stat-value">{Math.floor(city.resources.food)}</span>
                <span className="stat-label">🪵</span>
                <span className="stat-value">{Math.floor(city.resources.timber)}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">⚙️</span>
                <span className="stat-value">{Math.floor(city.resources.metal)}</span>
                <span className="stat-label">💰</span>
                <span className="stat-value">{Math.floor(city.resources.wealth)}</span>
              </div>
            </div>

            <div className="city-buildings">
              🏢 {city.buildings_count} building{city.buildings_count !== 1 ? "s" : ""}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CitySwitcher;