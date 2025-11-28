/**
 * Tab Container Component
 * Provides a reusable tabbed interface
 */

import React, { useState } from "react";
import "./styles/TabContainer.css";

export interface TabDefinition {
  id: string;
  label: string;
  icon?: string;
  content: React.ReactNode;
  disabled?: boolean;
}

interface Props {
  tabs: TabDefinition[];
  defaultTabId?: string;
}

const TabContainer: React.FC<Props> = ({ tabs, defaultTabId }) => {
  const [activeTabId, setActiveTabId] = useState(defaultTabId || tabs[0]?.id || "");

  const activeTab = tabs.find((t) => t.id === activeTabId);

  return (
    <div className="tab-container">
      {/* Tab Navigation Bar */}
      <div className="tab-nav-bar">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab-button ${activeTabId === tab.id ? "active" : ""} ${
              tab.disabled ? "disabled" : ""
            }`}
            onClick={() => !tab.disabled && setActiveTabId(tab.id)}
            disabled={tab.disabled}
          >
            {tab.icon && <span className="tab-icon">{tab.icon}</span>}
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab && <div className="tab-pane">{activeTab.content}</div>}
      </div>
    </div>
  );
};

export default TabContainer;