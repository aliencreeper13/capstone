// Auto-generated TypeScript interfaces from Python backend classes
// DO NOT EDIT MANUALLY - regenerate using generate_ts_interfaces.py

// ===== Type Aliases =====

type EventType = "battle_tick" | "battle_result" | "city_captured" | "building_completed" | "unit_created" | "resource_change" | "custom";

// Core Game Entity Interfaces

// ===== Unit Type Definitions =====

interface BuildingType {
  name: string;
  size: number;
  effect: Effect;
  job_requirements: JobRequirements;
  description: string;
  job_num_ticks: number;
}

interface TroopType {
  name: string;
  size: number;
  effect: Effect;
  job_requirements: JobRequirements;
  description: string;
  job_num_ticks: number;
  base_attributes: CombatAttributes;
}

interface UnitType {
  name: string;
  size: number;
  effect: Effect;
  job_requirements: JobRequirements;
  description: string;
  job_num_ticks: number;
}

// ===== Core Entities =====

interface City {
  allegiance: Empire;
  current_tick: number | null;
  autonomy: number | null;
  defense: number | null;
  size: number | null;
  space_left: number | null;
  hitpoints: number | null;
  protection: number | null;
  expendable_resource_capacities: ExpendableCityResources | null;
  population_limit: number | null;
  knowledge: number | null;
  expendable_city_resource_pct_increase: ExpendableCityResources | null;
  expendable_city_resource_factor: ExpendableCityResources | null;
  total_population: number | null;
  employable_population: number | null;
  morale: number | null;
}

interface Empire {
  allegiance: Empire;
  capital: City | null;
  current_tick: number | null;
  working_age: number | null;
  retirement_age: number | null;
  knowledge: number | null;
  efficiency: number | null;
  corruption: number | null;
  autonomy: number | null;
  game_events: GameEvent[] | null;
}

interface Game {
  current_tick: number;
}

// ===== Unit Instances =====

interface Unit {
}

interface Building {
  allegiance: Empire | null;
}

interface Troop {
  allegiance: Empire | null;
  current_attributes: CombatAttributes;
  current_morale: number;
  max_attributes: CombatAttributes;
  is_dead: boolean;
}

// ===== Resources =====

interface ExpendableCityResources {
  food: number;
  timber: number;
  wealth: number;
  metal: number;
}

interface ExpendableEmpireResources {
  efficiency: number;
  knowledge: number;
}

interface Population {
  population_by_age: number[];
  employable_population_by_age: number[];
  employed_population_by_age: number[];
  max_lifespan: number;
}

interface SocietalResources {
  population: Population;
  morale: number;
}

// ===== Effects =====

interface Effect {
  duration_in_ticks: number;
  expendable_city_resources_per_tick: ExpendableCityResources;
  expendable_empire_resources_per_tick: ExpendableEmpireResources;
  expendable_city_resources_pct_increase: ExpendableCityResources;
  expendable_empire_resources_pct_increase: ExpendableEmpireResources;
  theoretical_new_employable_per_tick: number;
  raw_morale_per_tick: number;
  raw_efficiency_per_tick: number;
  city_base_defense_offered: number;
  city_base_protection_offered: number;
  city_hitpoint_regeneration_per_tick: number;
  expendable_city_resource_capacities_offered: ExpendableCityResources;
  population_capacity_offered: number;
  new_people_per_tick: number;
  dead_people_per_tick: number;
  max_lifespan_increase: number;
  capital_effect: boolean;
  specific_units_contingent_on: Unit[];
  job_speedup_multiplier: number;
  effect_id: number | null;
  contingency_check: any;
  dynamic_expendable_city_resources_per_tick: any;
  dynamic_expendable_empire_resources_per_tick: any;
  dynamic_theoretical_new_employable_per_tick: any;
  dynamic_morale_per_tick: any;
  dynamic_raw_efficiency_per_tick: any;
  dynamic_city_hitpoint_regeneration_per_tick: any;
  dynamic_new_people_per_tick: any;
  dynamic_dead_people_per_tick: any;
  dynamic_job_speedup_multiplier: any;
}

interface Ideology {
  effects: Effect[];
}

// ===== Events =====

interface GameEvent {
  type: EventType;
  unix_timestamp: number;
  source: string;
  description: string;
  data: Record<string, any>;
}

// ===== Other Interfaces =====

interface CombatAttributes {
  hitpoints: number;
  speed: number;
  damage_per_tick: number;
  morale: number;
}

interface ContingentOnInfo {
  unit_class: UnitType;
  minimum_level_needed: number;
}

interface JobRequirements {
  knowledge_level1: number;
  expendable_city_resources_level1: ExpendableCityResources;
  workers_needed_level1: number;
  specific_units_contingent_on: Unit[];
  unit_types_contingent_on: ContingentOnInfo[];
  max_per_city: number | null;
  exponent: number;
}


export {}