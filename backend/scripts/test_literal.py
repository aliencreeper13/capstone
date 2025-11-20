#!/usr/bin/env python3
python_type = 'Literal["battle_tick", "battle_result", "city_captured"]'
print('Input:', repr(python_type))
start = python_type.index('[')
end = python_type.rindex(']')
literal_content = python_type[start+1:end]
print('Literal content:', repr(literal_content))
values = [v.strip().strip('"').strip("'") for v in literal_content.split(',')]
print('Values:', values)
result = ' | '.join(f'"{v}"' for v in values)
print('Result:', repr(result))