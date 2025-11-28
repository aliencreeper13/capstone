/**
 * Population Details Component
 * Displays detailed population information for a city
 */

import React from "react";
import { CityData } from "../types/gameState";
import "./styles/PopulationDetails.css";

interface Props {
  city: CityData;
}

const PopulationDetails: React.FC<Props> = ({ city }) => {
  const { population } = city;
  const unemployed = population.employable - population.employed;
  const employablePercent = population.total > 0
    ? (population.employable / population.total) * 100
    : 0;
  const employedPercent = population.employable > 0
    ? (population.employed / population.employable) * 100
    : 0;

  return (
    <div className="population-details">
      <h3>Population Overview</h3>
      
      <div className="population-stat">
        <div className="stat-label">Total Population</div>
        <div className="stat-value">{population.total}</div>
      </div>

      <div className="population-stat">
        <div className="stat-label">Employable</div>
        <div className="stat-value">
          {population.employable}
          <span className="percent">
            ({employablePercent.toFixed(1)}%)
          </span>
        </div>
      </div>

      <div className="population-stat">
        <div className="stat-label">Employed</div>
        <div className="stat-value">
          {population.employed}
          <span className="percent">
            ({employedPercent.toFixed(1)}%)
          </span>
        </div>
      </div>

      <div className="population-stat">
        <div className="stat-label">Unemployed</div>
        <div className="stat-value">{unemployed}</div>
      </div>

      <div className="population-progress">
        <div className="progress-bar">
          <div
            className="progress-fill employed"
            style={{ width: `${employedPercent}%` }}
          />
          <div
            className="progress-fill unemployed"
            style={{ width: `${100 - employedPercent}%` }}
          />
        </div>
        <div className="progress-labels">
          <span>Employed</span>
          <span>Unemployed</span>
        </div>
      </div>
    </div>
  );
};

export default PopulationDetails;