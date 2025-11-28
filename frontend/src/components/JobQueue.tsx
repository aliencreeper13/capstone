/**
 * Job Queue Component
 * Displays active construction/upgrade jobs with progress bars
 */

import React from "react";
import "./styles/JobQueue.css";

interface Job {
  id: string;
  building_type: string;
  ticks_remaining: number;
  ticks_total: number;
  progress_percent: number;
  is_upgrade: boolean;
}

interface Props {
  jobs: Job[];
}

const JobIcons: Record<string, string> = {
  farm: "🌾",
  housing: "🏠",
  barracks: "⚔️",
  school: "📚",
  university: "🎓",
  market: "🏪",
  temple: "⛪",
  tower: "🗼",
  wall: "🧱",
  library: "📖",
  granary: "🏪",
  woodcutterscamp: "🌲",
  lumberyard: "🌲",
  mine: "⛏️",
  hospital: "⚕️",
  default: "🏗️",
};

const getJobIcon = (name: string): string => {
  const normalized = name.toLowerCase();
  return (
    JobIcons[normalized] ||
    Object.entries(JobIcons).find(([key]) => normalized.includes(key))?.[1] ||
    JobIcons.default
  );
};

const JobQueue: React.FC<Props> = ({ jobs }) => {
  if (jobs.length === 0) {
    return (
      <div className="job-queue">
        <h3>🏗️ Construction Queue</h3>
        <div className="empty-state">No active jobs</div>
      </div>
    );
  }

  return (
    <div className="job-queue">
      <h3>🏗️ Construction Queue ({jobs.length})</h3>
      <div className="jobs-container">
        {jobs.map((job) => (
          <div key={job.id} className="job-card">
            <div className="job-header">
              <span className="icon">{getJobIcon(job.building_type)}</span>
              <div className="job-title">
                <span className="name">{job.building_type}</span>
                <span className="badge">
                  {job.is_upgrade ? "Upgrade" : "Building"}
                </span>
              </div>
            </div>
            
            <div className="progress-container">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${job.progress_percent}%` }}
                />
              </div>
              <div className="progress-text">
                <span className="percentage">{Math.round(job.progress_percent)}%</span>
                <span className="ticks">
                  {job.ticks_remaining}/{job.ticks_total} ticks
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default JobQueue;