import React, { useEffect, useState } from "react";

interface Resources {
  food: number;
  timber: number;
  metal: number;
  wealth: number;
}

interface CityData {
  total_population: number;
  resources: Resources;
  morale: number;
  // In the future: buildings, etc.
}

const CityViewer: React.FC = () => {
  const [cityData, setCityData] = useState<CityData | null>(null);

  useEffect(() => {
    // Example WebSocket endpoint — replace with your own
    const ws = new WebSocket("ws://localhost:8080/ws/city");

    ws.onopen = () => {
      console.log("✅ Connected to city WebSocket");
    };

    ws.onmessage = (event) => {
      try {
        const data: CityData = JSON.parse(event.data);
        setCityData(data);
      } catch (err) {
        console.error("Error parsing city data:", err);
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

    ws.onclose = () => {
      console.log("❌ City WebSocket disconnected");
    };

    return () => {
      ws.close();
    };
  }, []);

  if (!cityData) {
    return <div>Loading city data...</div>;
  }

  const { total_population, resources, morale } = cityData;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2>🏙️ City Overview</h2>
        <div style={styles.stats}>
          <div>Population: {total_population}</div>
          <div>Morale: {morale}</div>
        </div>
        <div style={styles.resources}>
          <strong>Resources:</strong>
          <div>🍞 Food: {resources.food}</div>
          <div>🪓 Timber: {resources.timber}</div>
          <div>⛏️ Metal: {resources.metal}</div>
          <div>💰 Wealth: {resources.wealth}</div>
        </div>
      </div>

      {/* Placeholder for city visual (e.g. map/buildings/etc.) */}
      <div style={styles.cityView}>
        <em>City view placeholder — buildings will go here</em>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    fontFamily: "sans-serif",
    backgroundColor: "#f4f4f4",
    padding: "1rem",
    borderRadius: "8px",
    width: "400px",
    margin: "1rem auto",
    boxShadow: "0 2px 5px rgba(0,0,0,0.1)",
  },
  header: {
    marginBottom: "1rem",
  },
  stats: {
    display: "flex",
    justifyContent: "space-between",
    marginBottom: "0.5rem",
  },
  resources: {
    backgroundColor: "#fff",
    padding: "0.5rem",
    borderRadius: "4px",
    boxShadow: "inset 0 0 2px rgba(0,0,0,0.1)",
  },
  cityView: {
    height: "200px",
    backgroundColor: "#dfe6e9",
    borderRadius: "4px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#555",
  },
};

export default CityViewer;