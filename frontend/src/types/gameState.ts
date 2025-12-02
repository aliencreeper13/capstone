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

export interface BuildingEffect {
  food_per_tick: number;
  timber_per_tick: number;
  metal_per_tick: number;
  wealth_per_tick: number;
  knowledge_per_tick: number;
  morale_per_tick: number;
  food_storage: number;
  timber_storage: number;
  metal_storage: number;
  wealth_storage: number;
  population_capacity: number;
  defense: number;
  protection: number;
  new_workers_per_tick: number;
  new_population_per_tick: number;
  hp_regeneration_per_tick: number;
  max_lifespan_increase: number;
}

export interface UpgradeCost {
  food: number;
  timber: number;
  metal: number;
  wealth: number;
}

export interface Building {
  id: string;
  name: string;
  level: number;
  space_used: number;
  current_effect: BuildingEffect;
  next_level_effect: BuildingEffect;
  upgrade_cost: UpgradeCost;
}

// ===== Phase 4: Army Movement Types =====

export interface UnitComposition {
  type: string;      // "Settler", "Worker", "Soldier", etc.
  count: number;     // Number of units of this type
  name: string;      // Display name
}

export interface Army {
  id: string;
  name: string;
  unit_count: number;
  current_hp: number;
  max_hp: number;
  damage_per_tick: number;
  speed: number;               // Movement speed
  is_halted: boolean;          // Whether army is halted on a path
  is_on_path: boolean;         // Whether army is currently on a path
  // Phase 4 additions:
  units: UnitComposition[];    // Detailed unit composition
  position: number;            // Position on path (0-distance) or null if at node
  location: string;            // Current node name or "traveling"
  allegiance: string;          // Empire name
  morale: number;              // Army morale (0-100)
  eta_ticks?: number;          // Estimated ticks to destination (if moving)
  destination?: string;        // Destination node name (if moving)
  path_position?: number;      // Numeric position along path for rendering
  path_node1_coords?: [number, number];  // Starting node coordinates of path
  path_node2_coords?: [number, number];  // Ending node coordinates of path
}

export interface GameNodeData {
  id: string;
  coords: [number, number];
  size: number;                // Node visual size
  is_claimed: boolean;
  city_name?: string;           // City name if claimed
  stationed_armies: Army[];     // Armies at this node
}

export interface PathData {
  id: string;
  from_node: string;
  to_node: string;
  distance: number;
  armies_on_path: Array<{
    army: Army;
    position: number;           // Position along path
    eta_ticks: number;         // Ticks to destination
  }>;
}

export interface MapStructureData {
  nodes: GameNodeData[];
  paths: PathData[];
}

// ===== World Map Visualization Types =====

export interface WorldMapNode {
  id: string;
  coords: [number, number];
  size: number;
  is_claimed: boolean;
  is_friendly: boolean;
  city_name?: string;
}

export interface WorldMapPath {
  id: string;
  from_coords: [number, number];
  to_coords: [number, number];
  distance: number;
}

export interface WorldMapData {
  seed: number;
  size: [number, number];
  nodes: WorldMapNode[];
  paths: WorldMapPath[];
}

export interface CityData {
  coords: [number, number];
  name: string;
  population: Population;
  resources: Resources;
  resource_capacities: Resources;
  morale: number;
  defense: number;
  protection: number;
  hitpoints: number;
  max_hitpoints: number;
  buildings: Building[];
  armies?: Army[];
  space_used: number;
  space_total: number;
  max_space: number;
}

export interface EmpireData {
  name: string;
  num_cities?: number;
  total_population: Population;
  total_resources: Resources;
  knowledge: number;
  ideology: string;
  capital_name: string;
  efficiency: number;
  score: number;
}

export interface GameState {
  current_tick: number;
  empire: EmpireData;
  selected_city: CityData;
}