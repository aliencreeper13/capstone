/**
 * Resource Capacity Component
 * Displays current resources vs capacity for each resource type
 */

import React from "react";
import { CityData } from "../types/gameState";
import "./styles/ResourceCapacity.css";

interface Props {
  city: CityData;
}

interface ResourceInfo {
  name: string;
  key: keyof CityData["resources"];
  current: number;
  max: number;
  color: string;
}

const ResourceCapacity: React.FC<Props> = ({ city }) => {
  const resourceInfo: ResourceInfo[] = [
    { name: "Food", key: "food", current: city.resources.food, max: city.resource_capacities.food, color: "#27ae60" },
    { name: "Timber", key: "timber", current: city.resources.timber, max: city.resource_capacities.timber, color: "#8b4513" },
    { name: "Metal", key: "metal", current: city.resources.metal, max: city.resource_capacities.metal, color: "#95a5a6" },
    { name: "Wealth", key: "wealth", current: city.resources.wealth, max: city.resource_capacities.wealth, color: "#f39c12" },
  ];

  return (
    <div className="resource-capacity">
      <h3>Resource Capacity</h3>
      
      <div className="resources-grid">
        {resourceInfo.map((resource) => {
          const usagePercent = resource.max > 0 ? (resource.current / resource.max) * 100 : 0;
          
          return (
            <div key={resource.key} className="resource-item">
              <div className="resource-header">
                <span className="resource-name">{resource.name}</span>
                <span className="resource-values">
                  {Math.round(resource.current)}/{Math.round(resource.max)}
                </span>
              </div>
              
              <div className="resource-bar">
                <div
                  className="resource-fill"
                  style={{
                    width: `${Math.min(usagePercent, 100)}%`,
                    backgroundColor: resource.color,
                  }}
                />
              </div>
              
              <div className="resource-percent">
                {usagePercent.toFixed(0)}% full
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ResourceCapacity;