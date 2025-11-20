"""
Generate TypeScript interfaces from Python classes with client_property decorators.

This script parses Python entity classes and generates corresponding TypeScript interfaces.
- public_client_properties become required fields
- private_client_properties become optional fields (can be null)

Usage:
    python generate_ts_interfaces.py
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set


class ClientPropertyExtractor(ast.NodeVisitor):
    """Extract client_property decorated methods from Python classes."""
    
    def __init__(self):
        self.classes: Dict[str, Dict] = {}
        self.current_class: Optional[str] = None
        self.current_class_node: Optional[ast.ClassDef] = None
        self.current_file: Optional[str] = None
        self.type_aliases: Dict[str, str] = {}  # Track type aliases like EventType
        self.all_processed_classes: Dict[str, List[str]] = {}  # Track all classes to detect inheritance
        
    def visit_ClassDef(self, node: ast.ClassDef):
        """Extract class definition."""
        self.current_class = node.name
        self.current_class_node = node
        
        # Extract base class names
        base_names = [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
        self.all_processed_classes[node.name] = base_names
        
        self.classes[node.name] = {
            'public_properties': [],
            'private_properties': [],
            'bases': base_names,
            'dataclass_fields': [],
            'class_attributes': [],  # Track class-level type annotations
            'is_dataclass': self._is_dataclass(node),
            'is_dataclass_game_object': self._inherits_from_dataclass_game_object(node),
            'inherits_from_unit': self._inherits_from_unit(node, base_names),
            'type_aliases': self.type_aliases,  # Pass type aliases to each class
        }
        self.generic_visit(node)
        self.current_class = None
    
    def _is_dataclass(self, node: ast.ClassDef) -> bool:
        """Check if class has @dataclass decorator."""
        for decorator in node.decorator_list:
            decorator_name = self._get_decorator_name(decorator)
            if decorator_name == 'dataclass':
                return True
        return False
    
    def _inherits_from_dataclass_game_object(self, node: ast.ClassDef) -> bool:
        """Check if class inherits from DataclassGameObject."""
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id == 'DataclassGameObject':
                    return True
            elif isinstance(base, ast.Attribute):
                if base.attr == 'DataclassGameObject':
                    return True
        return False
    
    def _inherits_from_unit(self, node: ast.ClassDef, base_names: List[str]) -> bool:
        """Check if class directly or indirectly inherits from Unit."""
        # Direct inheritance
        if 'Unit' in base_names:
            return True
        # Note: Full transitive check would require two-pass analysis
        # For now, we'll mark it if Unit is in bases
        return False
    
    def visit_Assign(self, node: ast.Assign):
        """Capture module-level type aliases like EventType = Literal[...]"""
        # Only capture top-level assignments (not inside classes)
        if self.current_class is None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    alias_name = target.id
                    # Capture Literal types
                    if isinstance(node.value, ast.Subscript):
                        if isinstance(node.value.value, ast.Name) and node.value.value.id == 'Literal':
                            alias_def = self._annotation_to_string(node.value)
                            self.type_aliases[alias_name] = alias_def
        
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Extract annotated assignments (dataclass fields or class attributes)."""
        if self.current_class is None:
            return
        
        if isinstance(node.target, ast.Name):
            field_name = node.target.id
            type_hint = self._annotation_to_string(node.annotation)
            
            # Check if it's a problematic type
            warnings = self._check_type_serialization(type_hint)
            
            # For dataclass fields
            if self.classes[self.current_class]['is_dataclass']:
                self.classes[self.current_class]['dataclass_fields'].append({
                    'name': field_name,
                    'type': type_hint,
                    'warnings': warnings,
                })
            # For Unit class attributes (non-dataclass, but inherit from Unit or ARE Unit)
            elif self.classes[self.current_class]['inherits_from_unit'] or self.current_class == 'Unit':
                # Skip private attributes (starting with _)
                if not field_name.startswith('_'):
                    self.classes[self.current_class]['class_attributes'].append({
                        'name': field_name,
                        'type': type_hint,
                        'warnings': warnings,
                    })
    
    def _check_type_serialization(self, type_hint: str) -> List[str]:
        """Check if a type might have serialization issues."""
        warnings = []
        problematic_types = ['Callable', 'function', 'Method', 'Any', 'datetime', 'date', 'time']
        
        for ptype in problematic_types:
            if ptype in type_hint:
                warnings.append(f"⚠️  {ptype} may not serialize to JSON")
        
        return warnings
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Extract function definitions with decorators."""
        if self.current_class is None:
            return
            
        for decorator in node.decorator_list:
            decorator_name = self._get_decorator_name(decorator)
            if decorator_name == 'public_client_property':
                type_hint = self._extract_return_type(node)
                self.classes[self.current_class]['public_properties'].append({
                    'name': node.name,
                    'type': type_hint
                })
            elif decorator_name == 'private_client_property':
                type_hint = self._extract_return_type(node)
                self.classes[self.current_class]['private_properties'].append({
                    'name': node.name,
                    'type': type_hint
                })
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extract decorator name from decorator node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return ""
    
    def _extract_return_type(self, node: ast.FunctionDef) -> str:
        """Extract return type annotation from function."""
        if node.returns is None:
            return "any"
        
        return self._annotation_to_string(node.returns)
    
    def _annotation_to_string(self, annotation: ast.expr) -> str:
        """Convert AST annotation to string."""
        if annotation is None:
            return "any"
        
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            value = annotation.value
            # Preserve quotes for string constants
            if isinstance(value, str):
                return f'"{value}"'
            return str(value)
        elif isinstance(annotation, ast.Attribute):
            return f"{self._annotation_to_string(annotation.value)}.{annotation.attr}"
        elif isinstance(annotation, ast.Subscript):
            # Handle generics like List[str], Dict[str, int], Optional[int]
            value = self._annotation_to_string(annotation.value)
            
            # Special handling for Literal - needs comma-separated values, not union
            if value == "Literal":
                if isinstance(annotation.slice, ast.Tuple):
                    # For Literal tuple, preserve as comma-separated list
                    values = [self._annotation_to_string(elt) for elt in annotation.slice.elts]
                    return f"Literal[{', '.join(values)}]"
                else:
                    # Single value Literal
                    slice_val = self._annotation_to_string(annotation.slice)
                    return f"Literal[{slice_val}]"
            
            slice_val = self._annotation_to_string(annotation.slice)
            
            if value == "Optional":
                return f"{slice_val} | null"
            elif value == "list":
                return f"{slice_val}[]"
            elif value == "List":
                return f"{slice_val}[]"
            elif value == "dict" or value == "Dict":
                # For Dict, return Python-style so _python_to_ts_type can convert properly
                if isinstance(annotation.slice, ast.Tuple):
                    key_type = self._annotation_to_string(annotation.slice.elts[0])
                    val_type = self._annotation_to_string(annotation.slice.elts[1])
                    return f"dict[{key_type}, {val_type}]"
                return "dict[str, Any]"
            else:
                return f"{value}<{slice_val}>"
        elif isinstance(annotation, ast.Tuple):
            # Union type or tuple - for non-Literal contexts
            types = [self._annotation_to_string(elt) for elt in annotation.elts]
            return " | ".join(types)
        else:
            # Fallback: convert node to code
            return ast.unparse(annotation) if hasattr(ast, 'unparse') else "any"


class TypeScriptGenerator:
    """Generate TypeScript interfaces from extracted class information."""
    
    # Mapping Python types to TypeScript types
    TYPE_MAPPING = {
        'int': 'number',
        'float': 'number',
        'str': 'string',
        'bool': 'boolean',
        'bool | None': 'boolean | null',
        'Optional': 'null',
        'List': 'any[]',
        'Dict': 'Record<string, any>',
        'None': 'null',
        'Any': 'any',
    }
    
    def __init__(self, type_aliases: Dict[str, str] = None, all_classes: Dict[str, Dict] = None):
        self.interfaces: Dict[str, str] = {}
        self.imports: Set[str] = set()
        self.type_aliases: Dict[str, str] = type_aliases or {}
        self.all_classes: Dict[str, Dict] = all_classes or {}
        
    def _collect_inherited_properties(self, class_name: str, visited: Set[str] = None) -> Tuple[List[Dict], List[Dict]]:
        """
        Recursively collect all client properties including inherited ones.
        Returns (public_properties, private_properties) lists.
        """
        if visited is None:
            visited = set()
        
        if class_name in visited or class_name not in self.all_classes:
            return [], []
        
        visited.add(class_name)
        
        # Collect from parent classes first
        public_props = []
        private_props = []
        for base in self.all_classes[class_name].get('bases', []):
            parent_public, parent_private = self._collect_inherited_properties(base, visited.copy())
            public_props.extend(parent_public)
            private_props.extend(parent_private)
        
        # Add this class's own properties (avoiding duplicates from inheritance)
        own_prop_names = {prop['name'] for prop in public_props + private_props}
        for prop in self.all_classes[class_name].get('public_properties', []):
            if prop['name'] not in own_prop_names:
                public_props.append(prop)
        
        for prop in self.all_classes[class_name].get('private_properties', []):
            if prop['name'] not in own_prop_names:
                private_props.append(prop)
        
        return public_props, private_props
    
    def generate_interface(self, class_name: str, class_info: Dict) -> str:
        """Generate TypeScript interface for a Python class."""
        lines = [f"interface {class_name} {{"]
        
        # If this is a DataclassGameObject with fields, use those
        if class_info.get('is_dataclass_game_object') and class_info.get('dataclass_fields'):
            # All dataclass fields are public (non-nullable)
            for field in class_info['dataclass_fields']:
                ts_type = self._python_to_ts_type(field['type'])
                lines.append(f"  {field['name']}: {ts_type};")
        else:
            # Collect inherited properties
            public_props, private_props = self._collect_inherited_properties(class_name)
            
            # Add public properties (required)
            for prop in public_props:
                ts_type = self._python_to_ts_type(prop['type'])
                lines.append(f"  {prop['name']}: {ts_type};")
            
            # Add private properties (optional, can be null)
            for prop in private_props:
                ts_type = self._python_to_ts_type(prop['type'])
                # Private properties can return null on unauthorized access
                if '| null' not in ts_type:
                    ts_type = f"{ts_type} | null"
                lines.append(f"  {prop['name']}: {ts_type};")
        
        lines.append("}")
        return "\n".join(lines)
    
    def generate_type_interface(self, class_name: str, class_info: Dict) -> str:
        """Generate TypeScript interface for class attributes (the 'Type' or 'Blueprint')."""
        type_name = f"{class_name}Type"
        lines = [f"interface {type_name} {{"]
        
        # Add class attributes (class-level type annotations)
        for attr in class_info.get('class_attributes', []):
            ts_type = self._python_to_ts_type(attr['type'])
            lines.append(f"  {attr['name']}: {ts_type};")
        
        lines.append("}")
        return "\n".join(lines)
    
    def _python_to_ts_type(self, python_type: str) -> str:
        """Convert Python type annotation to TypeScript."""
        python_type = python_type.strip()
        
        # Check if this is a known type alias - if so, return the alias name directly
        # (don't expand it; it will be defined separately)
        if python_type in self.type_aliases:
            return python_type
        
        # Direct mappings
        if python_type in self.TYPE_MAPPING:
            return self.TYPE_MAPPING[python_type]
        
        # Handle Callable types - these can't be serialized, so use any
        if 'Callable' in python_type:
            return 'any'
        
        # Handle Optional[X] -> X | null
        if python_type.startswith("Optional["):
            inner = python_type[9:-1]  # Extract X from Optional[X]
            return f"{self._python_to_ts_type(inner)} | null"
        
        # Handle list[X] or List[X] -> X[]
        if python_type.startswith("list[") or python_type.startswith("List["):
            start = python_type.index("[")
            inner = python_type[start+1:-1]
            return f"{self._python_to_ts_type(inner)}[]"
        
        # Handle custom Literal types (like EventType) - must come before union check!
        if python_type.startswith('Literal['):
            # Extract the literal values
            start = python_type.index('[')
            end = python_type.rindex(']')
            literal_content = python_type[start+1:end]
            # Convert string literals to union type
            values = [v.strip().strip('"').strip("'") for v in literal_content.split(',')]
            return ' | '.join(f'"{v}"' for v in values)
        
        # Handle dict[K, V] or Dict[K, V]
        if python_type.startswith("dict[") or python_type.startswith("Dict["):
            start = python_type.index("[")
            inner = python_type[start+1:-1]
            # Split by comma, but be careful with nested types
            parts = self._split_type_params(inner)
            if len(parts) == 2:
                key_type = self._python_to_ts_type(parts[0].strip())
                val_type = self._python_to_ts_type(parts[1].strip())
                return f"Record<{key_type}, {val_type}>"
            return "Record<string, any>"
        
        # Handle union types X | Y
        if " | " in python_type:
            parts = python_type.split(" | ")
            return " | ".join(self._python_to_ts_type(p.strip()) for p in parts)
        
        # Common Python class names that map to specific types
        common_mappings = {
            'ExpendableCityResources': 'ExpendableCityResources',
            'ExpendableEmpireResources': 'ExpendableEmpireResources',
            'Population': 'Population',
            'SocietalResources': 'SocietalResources',
            'Empire': 'Empire',
            'City': 'City',
            'Army': 'Army',
            'Unit': 'Unit',
            'Building': 'Building',
            'Troop': 'Troop',
            'GameEvent': 'GameEvent',
            'Ideology': 'Ideology',
            'Effect': 'Effect',
            'Game': 'Game',
            'JobRequirements': 'JobRequirements'
        }
        
        if python_type in common_mappings:
            return common_mappings[python_type]
        
        # Replace Python base types with TypeScript equivalents
        type_replacements = {
            'int': 'number',
            'float': 'number',
            'str': 'string',
            'bool': 'boolean',
            'Any': 'any',  # Special case: Any -> any (lowercase)
        }
        
        for py_type, ts_type in type_replacements.items():
            if python_type == py_type:
                return ts_type
            elif python_type.startswith(f'{py_type}['):
                python_type = python_type.replace(py_type, ts_type, 1)
                # Recursively call to handle things like int[] -> number[]
                if '[' in python_type:
                    return self._python_to_ts_type(python_type)
                return python_type
        
        # For unknown types, preserve the name (assuming it's a class name or type alias)
        return python_type
    
    def _split_type_params(self, params: str) -> List[str]:
        """Split type parameters by comma, respecting nested brackets."""
        result = []
        current = []
        bracket_depth = 0
        
        for char in params:
            if char in '[<':
                bracket_depth += 1
                current.append(char)
            elif char in ']>':
                bracket_depth -= 1
                current.append(char)
            elif char == ',' and bracket_depth == 0:
                result.append(''.join(current).strip())
                current = []
            else:
                current.append(char)
        
        if current:
            result.append(''.join(current).strip())
        
        return result


def find_python_files(directory: str) -> List[str]:
    """Find all Python files in entities, systems, and gameplay directories."""
    files = []
    for pattern in ['entities', 'systems', 'gameplay', 'core']:
        pattern_path = os.path.join(directory, pattern)
        if os.path.exists(pattern_path):
            for file in Path(pattern_path).glob('*.py'):
                if not file.name.startswith('__'):
                    files.append(str(file))
    return files


def extract_classes_from_file(filepath: str) -> Dict[str, Dict]:
    """Parse a Python file and extract class information."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        extractor = ClientPropertyExtractor()
        extractor.visit(tree)
        
        return extractor.classes
    except Exception as e:
        print(f"Warning: Could not parse {filepath}: {e}")
        return {}


def build_inheritance_hierarchy(all_classes: Dict[str, Dict]) -> Dict[str, bool]:
    """
    Build a mapping of which classes transitively inherit from Unit.
    Returns {class_name: inherits_from_unit} dict.
    """
    inherits_from_unit_map = {}
    
    def is_unit_subclass(class_name: str, visited: Set[str] = None) -> bool:
        """Recursively check if a class transitively inherits from Unit."""
        if visited is None:
            visited = set()
        
        if class_name in visited:
            return False  # Circular inheritance - shouldn't happen
        
        if class_name not in all_classes:
            return False  # Class not found
        
        visited.add(class_name)
        
        if class_name == 'Unit':
            return True
        
        bases = all_classes[class_name].get('bases', [])
        for base in bases:
            if is_unit_subclass(base, visited.copy()):
                return True
        
        return False
    
    for class_name in all_classes:
        inherits_from_unit_map[class_name] = is_unit_subclass(class_name)
    
    return inherits_from_unit_map


def collect_inherited_class_attributes(class_name: str, all_classes: Dict[str, Dict], visited: Set[str] = None) -> List[Dict]:
    """
    Recursively collect all class attributes including inherited ones.
    Returns list of {name, type, warnings} dicts.
    """
    if visited is None:
        visited = set()
    
    if class_name in visited or class_name not in all_classes:
        return []
    
    visited.add(class_name)
    
    # Collect from parent classes first (to maintain inheritance order)
    all_attrs = []
    for base in all_classes[class_name].get('bases', []):
        all_attrs.extend(collect_inherited_class_attributes(base, all_classes, visited.copy()))
    
    # Add this class's own attributes (avoiding duplicates from inheritance)
    own_attr_names = {attr['name'] for attr in all_attrs}
    for attr in all_classes[class_name].get('class_attributes', []):
        if attr['name'] not in own_attr_names:
            all_attrs.append(attr)
    
    return all_attrs


def main():
    """Main entry point."""
    # Determine paths
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    frontend_dir = backend_dir.parent / 'frontend'
    output_dir = frontend_dir / 'src' / 'types'
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find Python files
    python_files = find_python_files(str(backend_dir))
    
    print(f"Found {len(python_files)} Python files")
    
    # Extract all classes
    all_classes: Dict[str, Dict] = {}
    all_type_aliases: Dict[str, str] = {}
    for filepath in python_files:
        classes = extract_classes_from_file(filepath)
        all_classes.update(classes)
        # Collect type aliases from all files
        for class_info in classes.values():
            all_type_aliases.update(class_info.get('type_aliases', {}))
    
    # Build inheritance hierarchy and update class info
    inheritance_map = build_inheritance_hierarchy(all_classes)
    for class_name, inherits_from_unit in inheritance_map.items():
        if class_name in all_classes:
            all_classes[class_name]['inherits_from_unit'] = inherits_from_unit
    
    print(f"Found {len(all_classes)} classes with client_properties")
    
    if not all_classes:
        print("No classes with client_properties found!")
        return
    
    # Focus on essential classes for frontend
    essential_classes = [
        'City', 'Empire', 'Army', 'Unit', 'Building',
        'Troop', 'GameEvent', 'Game', 'Ideology',
        'ExpendableCityResources', 'ExpendableEmpireResources',
        'Population', 'SocietalResources', 'Effect', 'JobRequirements', 
        'ContingentOnInfo', 'CombatAttributes'
    ]
    
    # Generate interfaces
    generator = TypeScriptGenerator(type_aliases=all_type_aliases, all_classes=all_classes)
    generated_interfaces = {}
    generated_type_interfaces = {}  # Store Type interfaces separately
    serialization_warnings = {}
    
    for class_name in all_classes:
        if class_name in essential_classes:
            class_info = all_classes[class_name]
            
            # Generate instance interface
            interface_code = generator.generate_interface(class_name, class_info)
            generated_interfaces[class_name] = interface_code
            
            # Generate Type interface for all Unit subclasses (including those with inherited attributes)
            if class_info.get('inherits_from_unit'):
                # Collect all class attributes including inherited ones
                all_attrs = collect_inherited_class_attributes(class_name, all_classes)
                if all_attrs:  # Only generate if there are class attributes to show
                    # Create a temporary class_info with collected attributes
                    type_class_info = class_info.copy()
                    type_class_info['class_attributes'] = all_attrs
                    type_interface_code = generator.generate_type_interface(class_name, type_class_info)
                    generated_type_interfaces[class_name] = type_interface_code
            
            # Collect serialization warnings
            warnings = []
            for field in class_info.get('dataclass_fields', []):
                warnings.extend(field.get('warnings', []))
            
            if warnings:
                serialization_warnings[class_name] = warnings
    
    # Generate type alias definitions in TypeScript format
    type_alias_defs = {}
    if all_type_aliases:
        for alias_name, alias_def in all_type_aliases.items():
            # Convert the Literal definition to TypeScript union type
            if alias_def.startswith('Literal['):
                start = alias_def.index('[')
                end = alias_def.rindex(']')
                literal_content = alias_def[start+1:end]
                # The values should already have quotes from _annotation_to_string
                # Just split by comma and join with pipe
                values = [v.strip() for v in literal_content.split(',')]
                ts_union = ' | '.join(values)
                type_alias_defs[alias_name] = f"type {alias_name} = {ts_union};"
    
    # Write main interfaces file
    output_file = output_dir / 'GameEntities.ts'
    
    interface_content = "// Auto-generated TypeScript interfaces from Python backend classes\n"
    interface_content += "// DO NOT EDIT MANUALLY - regenerate using generate_ts_interfaces.py\n\n"
    
    # Add type aliases first
    if type_alias_defs:
        interface_content += "// ===== Type Aliases =====\n\n"
        for alias_name, alias_def in sorted(type_alias_defs.items()):
            interface_content += alias_def + "\n"
        interface_content += "\n"
    
    # Add imports if needed (can be expanded)
    interface_content += "// Core Game Entity Interfaces\n\n"
    
    # Group interfaces by category for readability
    categories = {
        'Unit Type Definitions': ['Unit', 'Building', 'Troop'],
        'Core Entities': ['City', 'Empire', 'Game', 'Army'],
        'Unit Instances': ['Unit', 'Building', 'Troop'],
        'Resources': ['ExpendableCityResources', 'ExpendableEmpireResources', 'Population', 'SocietalResources'],
        'Effects': ['Effect', 'Ideology'],
        'Events': ['GameEvent'],
    }
    
    # First, add Type interfaces for Unit classes
    type_classes_with_types = sorted(generated_type_interfaces.keys())
    if type_classes_with_types:
        interface_content += "// ===== Unit Type Definitions =====\n\n"
        for class_name in type_classes_with_types:
            interface_content += generated_type_interfaces[class_name] + "\n\n"
    
    # Then add instance interfaces by category
    categories_to_output = {
        'Core Entities': ['City', 'Empire', 'Game', 'Army'],
        'Unit Instances': ['Unit', 'Building', 'Troop'],
        'Resources': ['ExpendableCityResources', 'ExpendableEmpireResources', 'Population', 'SocietalResources'],
        'Effects': ['Effect', 'Ideology'],
        'Events': ['GameEvent'],
    }
    
    for category, class_names in categories_to_output.items():
        # Only add category header if there are classes to output
        classes_to_output = [c for c in class_names if c in generated_interfaces]
        if classes_to_output:
            interface_content += f"// ===== {category} =====\n\n"
            for class_name in classes_to_output:
                interface_content += generated_interfaces[class_name] + "\n\n"
    
    # Add any remaining classes not in categories
    remaining = set(generated_interfaces.keys()) - set(sum(categories_to_output.values(), []))
    if remaining:
        interface_content += "// ===== Other Interfaces =====\n\n"
        for class_name in sorted(remaining):
            interface_content += generated_interfaces[class_name] + "\n\n"
    
    # Write the file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(interface_content)
    
    print(f"\n✅ Generated TypeScript interfaces: {output_file}")
    print(f"✅ Generated instance interfaces for: {', '.join(sorted(generated_interfaces.keys()))}")
    if generated_type_interfaces:
        print(f"✅ Generated type/blueprint interfaces for: {', '.join(sorted(generated_type_interfaces.keys()))}")
    
    # Print summary
    total_public = sum(len(all_classes[c]['public_properties']) for c in generated_interfaces)
    total_private = sum(len(all_classes[c]['private_properties']) for c in generated_interfaces)
    total_dataclass_fields = sum(len(all_classes[c].get('dataclass_fields', [])) for c in generated_interfaces)
    total_class_attributes = sum(len(all_classes[c].get('class_attributes', [])) for c in generated_type_interfaces)
    dataclass_interfaces = [c for c in generated_interfaces if all_classes[c].get('is_dataclass_game_object')]
    
    print(f"\n📊 Summary:")
    print(f"   - Instance interfaces: {len(generated_interfaces)}")
    print(f"   - Type/Blueprint interfaces: {len(generated_type_interfaces)}")
    print(f"   - Client property interfaces: {len(generated_interfaces) - len(dataclass_interfaces)}")
    print(f"   - Dataclass interfaces: {len(dataclass_interfaces)}")
    print(f"   - Total public properties: {total_public}")
    print(f"   - Total private properties: {total_private}")
    print(f"   - Total dataclass fields: {total_dataclass_fields}")
    print(f"   - Total class attributes: {total_class_attributes}")
    print(f"   - Output file: {output_file}")
    
    # Print serialization warnings if any
    if serialization_warnings:
        print(f"\n⚠️  SERIALIZATION WARNINGS:")
        for class_name, warnings in serialization_warnings.items():
            print(f"   {class_name}:")
            for warning in warnings:
                print(f"      {warning}")


if __name__ == '__main__':
    main()