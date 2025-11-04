/**
 * Game API Service
 * Handles communication with the backend
 */

import { GameState } from "../types/gameState";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

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
   * Get mock/demo game state for development
   */
  static getMockGameState(): GameState {
    return {
      current_tick: 0,
      empire: {
        name: "Demo Empire",
        cities: [],
        total_population: { total: 0, employable: 0, employed: 0 },
        total_resources: { food: 0, timber: 0, metal: 0, wealth: 0 },
        knowledge: 0,
        ideology: "Neutral",
        capital_name: "Capital City",
      },
      selected_city: {
        coords: [0, 0],
        name: "Capital City",
        population: { total: 1000, employable: 500, employed: 300 },
        resources: { food: 100, timber: 50, metal: 25, wealth: 200 },
        resource_capacities: { food: 500, timber: 300, metal: 150, wealth: 1000 },
        morale: 50,
        defense: 100,
        hitpoints: 100,
        max_hitpoints: 100,
        buildings: [
          { id: "farm_1", name: "Farm", level: 1, space_used: 1 },
          { id: "house_1", name: "Housing", level: 2, space_used: 2 },
          { id: "barracks_1", name: "Barracks", level: 1, space_used: 1 },
        ],
        armies: [
          {
            id: "army_1",
            name: "City Guard",
            unit_count: 50,
            current_hp: 100,
            max_hp: 100,
            damage_per_tick: 15,
          },
        ],
        space_used: 4,
        space_total: 5,
      },
    };
  }
}