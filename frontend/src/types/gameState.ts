/**
 * Type definitions for the game state
 * Mirrors the backend Python data structures
 */

export interface Resources {
  food: number;
  timber: number;
  metal: number;
  wealth: number;
}

export interface Population {
  total: number;
  employable: number;
  employed: number;
}

export interface Building {
  id: string;
  name: string;
  level: number;
  space_used: number;
}

export interface Army {
  id: string;
  name: string;
  unit_count: number;
  current_hp: number;
  max_hp: number;
  damage_per_tick: number;
}

export interface CityData {
  coords: [number, number];
  name: string;
  population: Population;
  resources: Resources;
  resource_capacities: Resources;
  morale: number;
  defense: number;
  hitpoints: number;
  max_hitpoints: number;
  buildings: Building[];
  armies?: Army[]; // Optional: not currently provided by backend
  space_used: number;
  space_total: number;
}

export interface EmpireData {
  name: string;
  cities?: CityData[]; // Optional: not currently provided by backend (single city per empire)
  total_population: Population;
  total_resources: Resources;
  knowledge: number;
  ideology: string;
  capital_name: string;
}

export interface GameState {
  current_tick: number;
  empire: EmpireData;
  selected_city: CityData;
}