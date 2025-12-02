/**
 * Game API Service
 * Handles communication with the backend
 */

import { GameState, Army, MapStructureData, GameNodeData, WorldMapData } from "../types/gameState";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export interface BuildingRequirements {
  resources: Record<string, number>;
  workers: number;
  knowledge: number | null;
}

export interface AvailableBuilding {
  name: string;
  size: number;
  description: string;
  job_num_ticks: number;
  category: string;  // e.g., "Economic", "Civilian", "Military"
  requirements: BuildingRequirements;
}

export interface ApiResponse<T = any> {
  status: string;
  message?: string;
  data?: T;
}

export class GameApiService {
  /**
   * Fetch the current game state
   */
  static async getGameState(): Promise<GameState> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/game/state`);
      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Failed to fetch game state:", error);
      throw error;
    }
  }

  /**
   * Poll the game state at regular intervals
   */
  static subscribeToGameState(
    callback: (state: GameState) => void,
    intervalMs: number = 1000
  ): () => void {
    const interval = setInterval(async () => {
      try {
        const state = await this.getGameState();
        callback(state);
      } catch (error) {
        console.error("Error fetching game state in subscription:", error);
      }
    }, intervalMs);

    // Return unsubscribe function
    return () => clearInterval(interval);
  }

  /**
   * Create a new building in the capital city
   */
  static async createBuilding(buildingType: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/building/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ building_type: buildingType }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Failed to create building: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to create building:", error);
      throw error;
    }
  }

  /**
   * Demolish a building
   */
  static async demolishBuilding(buildingId: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/building/action`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ building_id: buildingId, action: "demolish" }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to demolish building");
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to demolish building:", error);
      throw error;
    }
  }

  /**
   * Upgrade a building
   */
  static async upgradeBuilding(buildingId: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/building/action`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ building_id: buildingId, action: "upgrade" }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to upgrade building");
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to upgrade building:", error);
      throw error;
    }
  }

  /**
   * Expand city size (building space)
   */
  static async expandCity(sizeIncrease: number = 1): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/city/expand`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ size_increase: sizeIncrease }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to expand city");
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to expand city:", error);
      throw error;
    }
  }

  /**
   * Transfer resources from the selected city to a target city
   */
  static async transferResources(
    targetCityId: number,
    food: number = 0,
    timber: number = 0,
    metal: number = 0,
    wealth: number = 0
  ): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/city/transfer`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          target_city_id: targetCityId,
          food,
          timber,
          metal,
          wealth,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to transfer resources");
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to transfer resources:", error);
      throw error;
    }
  }

  /**
   * Get available building types
   */
  static async getAvailableBuildings(): Promise<AvailableBuilding[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/buildings/available`);

      if (!response.ok) {
        throw new Error(`Failed to fetch buildings: ${response.statusText}`);
      }

      const data = await response.json();
      return data.buildings || [];
    } catch (error) {
      console.error("Failed to fetch available buildings:", error);
      throw error;
    }
  }

  /**
   * Get active jobs for the selected city
   */
  static async getCityJobs(): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/city/jobs`);
      if (!response.ok) {
        throw new Error(`Failed to fetch city jobs: ${response.statusText}`);
      }
      const data = await response.json();
      return data.jobs || [];
    } catch (error) {
      console.error("Failed to fetch city jobs:", error);
      throw error;
    }
  }

  /**
   * Get recent game events
   */
  static async getGameEvents(limit: number = 50): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/events?limit=${limit}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch game events: ${response.statusText}`);
      }
      const data = await response.json();
      return data.events || [];
    } catch (error) {
      console.error("Failed to fetch game events:", error);
      throw error;
    }
  }

  /**
   * Get available mobile units (troops and passive units) for creation
   */
  static async getAvailableMobileUnits(): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/mobile-units/available`);
      if (!response.ok) {
        throw new Error(`Failed to fetch available mobile units: ${response.statusText}`);
      }
      const data = await response.json();
      return {
        troops: data.troops || [],
        passive_units: data.passive_units || [],
      };
    } catch (error) {
      console.error("Failed to fetch available mobile units:", error);
      throw error;
    }
  }

  /**
   * Create a mobile unit (troop or passive unit)
   */
  static async createMobileUnit(unitType: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/mobile-units/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ unit_type: unitType }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Failed to create mobile unit: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to create mobile unit:", error);
      throw error;
    }
  }

  /**
   * Get world map visualization
   */
  static async getMapVisualization(): Promise<Blob> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/map/visualization`);
      if (!response.ok) {
        throw new Error(`Failed to fetch map visualization: ${response.statusText}`);
      }
      return await response.blob();
    } catch (error) {
      console.error("Failed to fetch map visualization:", error);
      throw error;
    }
  }

  /**
   * Execute a government action (costs wealth from capital)
   */
  static async executeGovernmentAction(actionId: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/government/action`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ action_id: actionId }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Failed to execute government action: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to execute government action:", error);
      throw error;
    }
  }

  /**
   * Get available government actions
   */
  static async getAvailableGovernmentActions(): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/government/available-actions`);
      if (!response.ok) {
        throw new Error(`Failed to fetch government actions: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Failed to fetch government actions:", error);
      throw error;
    }
  }

  /**
   * Get world map data for client-side rendering
   */
  static async getWorldMapData(): Promise<WorldMapData> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/map/worldmap-data`);
      if (!response.ok) {
        throw new Error(`Failed to fetch worldmap data: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Failed to fetch worldmap data:", error);
      throw error;
    }
  }

  // ========== Phase 4: Army Movement APIs ==========

  /**
   * Get all armies across the map
   */
  static async getArmies(): Promise<Army[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/armies`);
      if (!response.ok) {
        throw new Error(`Failed to fetch armies: ${response.statusText}`);
      }
      const data = await response.json();
      return data.armies || [];
    } catch (error) {
      console.error("Failed to fetch armies:", error);
      throw error;
    }
  }

  /**
   * Get complete map structure (nodes, paths, armies)
   */
  static async getMapStructure(): Promise<MapStructureData> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/map/structure`);
      if (!response.ok) {
        throw new Error(`Failed to fetch map structure: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Failed to fetch map structure:", error);
      throw error;
    }
  }

  /**
   * Get adjacent nodes (movement options) for a given node
   */
  static async getAdjacentNodes(nodeId: string): Promise<GameNodeData[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/gamenode/${nodeId}/adjacent`);
      if (!response.ok) {
        throw new Error(`Failed to fetch adjacent nodes: ${response.statusText}`);
      }
      const data = await response.json();
      return data.adjacent_nodes || [];
    } catch (error) {
      console.error("Failed to fetch adjacent nodes:", error);
      throw error;
    }
  }

  /**
   * Move an army to an adjacent node
   */
  static async moveArmy(armyId: string, destinationNodeId: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/armies/${armyId}/move`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        // include army_id because FastAPI model expects it in the body
        body: JSON.stringify({ army_id: armyId, destination_node_id: destinationNodeId }),
      });

      if (!response.ok) {
        // Try to parse JSON body safely and build a useful message
        let errorPayload: any = null;
        try {
          errorPayload = await response.json();
        } catch (parseErr) {
          // Non-JSON response
          throw new Error(`Failed to move army: ${response.status} ${response.statusText}`);
        }

        // Prefer common fields, otherwise stringify the payload
        const detail = errorPayload?.detail ?? errorPayload?.message ?? errorPayload;
        const msg = typeof detail === "string"
          ? detail
          : (detail === null || detail === undefined)
            ? `Failed to move army: ${response.status} ${response.statusText}`
            : JSON.stringify(detail);

        throw new Error(msg);
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to move army:", error);
      throw error;
    }
  }

  /**
   * Halt an army on a path
   */
  static async haltArmy(armyId: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/armies/${armyId}/halt`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Failed to halt army: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to halt army:", error);
      throw error;
    }
  }

  /**
   * Resume an army on a path
   */
  static async resumeArmy(armyId: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/armies/${armyId}/resume`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Failed to resume army: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to resume army:", error);
      throw error;
    }
  }

  /**
   * Reverse an army's direction on a path
   */
  static async reverseArmy(armyId: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/armies/${armyId}/reverse`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Failed to reverse army: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to reverse army:", error);
      throw error;
    }
  }

  /**
   * Get mock/demo game state for development
   */
  static getMockGameState(): GameState {
    return {
      current_tick: 0,
      empire: {
        name: "Demo Empire",
        num_cities: 1,
        total_population: { total: 0, employable: 0, employed: 0 },
        total_resources: { food: 0, timber: 0, metal: 0, wealth: 0 },
        knowledge: 0,
        ideology: "Neutral",
        capital_name: "Capital City",
        efficiency: 50,
        score: 1000,
      },
      selected_city: {
        coords: [0, 0],
        name: "Capital City",
        population: { total: 1000, employable: 500, employed: 300 },
        resources: { food: 100, timber: 50, metal: 25, wealth: 200 },
        resource_capacities: { food: 500, timber: 300, metal: 150, wealth: 1000 },
        morale: 50,
        defense: 100,
        protection: 50,
        hitpoints: 100,
        max_hitpoints: 100,
        buildings: [
          {
            id: "farm_1",
            name: "Farm",
            level: 1,
            space_used: 1,
            current_effect: {
              food_per_tick: 1,
              timber_per_tick: 0,
              metal_per_tick: 0,
              wealth_per_tick: 0,
              knowledge_per_tick: 0,
              morale_per_tick: 0,
              food_storage: 0,
              timber_storage: 0,
              metal_storage: 0,
              wealth_storage: 0,
              population_capacity: 0,
              defense: 0,
              protection: 0,
              new_workers_per_tick: 0,
              new_population_per_tick: 0,
              hp_regeneration_per_tick: 0,
              max_lifespan_increase: 0,
            },
            next_level_effect: {
              food_per_tick: 1.04,
              timber_per_tick: 0,
              metal_per_tick: 0,
              wealth_per_tick: 0,
              knowledge_per_tick: 0,
              morale_per_tick: 0,
              food_storage: 0,
              timber_storage: 0,
              metal_storage: 0,
              wealth_storage: 0,
              population_capacity: 0,
              defense: 0,
              protection: 0,
              new_workers_per_tick: 0,
              new_population_per_tick: 0,
              hp_regeneration_per_tick: 0,
              max_lifespan_increase: 0,
            },
            upgrade_cost: { food: 105, timber: 0, metal: 0, wealth: 0 },
          },
          {
            id: "house_1",
            name: "Housing",
            level: 2,
            space_used: 2,
            current_effect: {
              food_per_tick: 0,
              timber_per_tick: 0,
              metal_per_tick: 0,
              wealth_per_tick: 0,
              knowledge_per_tick: 0,
              morale_per_tick: 0,
              food_storage: 0,
              timber_storage: 0,
              metal_storage: 0,
              wealth_storage: 0,
              population_capacity: 100,
              defense: 0,
              protection: 0,
              new_workers_per_tick: 0,
              new_population_per_tick: 0,
              hp_regeneration_per_tick: 0,
              max_lifespan_increase: 0,
            },
            next_level_effect: {
              food_per_tick: 0,
              timber_per_tick: 0,
              metal_per_tick: 0,
              wealth_per_tick: 0,
              knowledge_per_tick: 0,
              morale_per_tick: 0,
              food_storage: 0,
              timber_storage: 0,
              metal_storage: 0,
              wealth_storage: 0,
              population_capacity: 104,
              defense: 0,
              protection: 0,
              new_workers_per_tick: 0,
              new_population_per_tick: 0,
              hp_regeneration_per_tick: 0,
              max_lifespan_increase: 0,
            },
            upgrade_cost: { food: 158, timber: 0, metal: 0, wealth: 0 },
          },
          {
            id: "barracks_1",
            name: "Barracks",
            level: 1,
            space_used: 1,
            current_effect: {
              food_per_tick: 0,
              timber_per_tick: 0,
              metal_per_tick: 0,
              wealth_per_tick: 0,
              knowledge_per_tick: 0,
              morale_per_tick: 0,
              food_storage: 0,
              timber_storage: 0,
              metal_storage: 0,
              wealth_storage: 0,
              population_capacity: 0,
              defense: 0,
              protection: 0,
              new_workers_per_tick: 0,
              new_population_per_tick: 0,
              hp_regeneration_per_tick: 0,
              max_lifespan_increase: 0,
            },
            next_level_effect: {
              food_per_tick: 0,
              timber_per_tick: 0,
              metal_per_tick: 0,
              wealth_per_tick: 0,
              knowledge_per_tick: 0,
              morale_per_tick: 0,
              food_storage: 0,
              timber_storage: 0,
              metal_storage: 0,
              wealth_storage: 0,
              population_capacity: 0,
              defense: 0,
              protection: 0,
              new_workers_per_tick: 0,
              new_population_per_tick: 0,
              hp_regeneration_per_tick: 0,
              max_lifespan_increase: 0,
            },
            upgrade_cost: { food: 0, timber: 105, metal: 52, wealth: 0 },
          },
        ],
        armies: [
          {
            id: "army_1",
            name: "City Guard",
            unit_count: 50,
            current_hp: 100,
            max_hp: 100,
            damage_per_tick: 15,
            speed: 3,
            is_halted: false,
            is_on_path: false,
            units: [{ type: "Soldier", count: 50, name: "Soldiers" }],
            position: 0,
            location: "Capital City",
            allegiance: "Demo Empire",
            morale: 75,
          },
        ],
        space_used: 4,
        space_total: 5,
        max_space: 20,
      },
    };
  }
}