// CityViewer.tsx
import React, { useEffect, useState } from "react";

interface SimpleCity {
  population: number;
  wealth: number;
}

const CityViewer: React.FC = () => {
  const [city, setCity] = useState<SimpleCity>({ population: 0, wealth: 0 });

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/city");

    ws.onmessage = (event: MessageEvent) => {
      const data: SimpleCity = JSON.parse(event.data);
      setCity(data);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    return () => ws.close();
  }, []);

  return (
    <div className="p-4 bg-gray-50 rounded-xl shadow-md max-w-sm">
      <h2 className="text-xl font-bold mb-2">🏙 City Overview</h2>
      <p><strong>Population:</strong> {city.population}</p>
      <p><strong>Wealth:</strong> {city.wealth}</p>
    </div>
  );
};

export default CityViewer;
