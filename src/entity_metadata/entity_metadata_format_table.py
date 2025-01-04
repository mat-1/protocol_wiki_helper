import json
from entity_metadata.mod import generate_metadata_names, read_text, replace_lines
from lib.mappings import Mappings

def update(burger_entities_data: dict, mappings: Mappings):
    text = read_text()
    parsed, start_i, end_i = parse(text)
    print(json.dumps(parsed))
    new_text = gen(parsed, burger_entities_data, mappings)
    replace_lines(new_text, start_i, end_i + 1)

def parse(text: str) -> tuple[dict, int, int]:
    start_i = None
    end_i = None

    in_table = False

    # map of like
    # { 'Rotations': {
    #   'value': '(Float, Float, Float)',
    #   'notes': 'rotation on x, rotation on y, rotation on z'
    # } }
    datas = {}

    current_type_name = None
    current_value = None
    current_notes = None

    for i, line in enumerate(text.splitlines()):
        if line == '{{Metadata type definition/begin}}':
            in_table = True
            start_i = i
            continue
        if in_table:
            if line.startswith('{{Metadata type definition|'):
                current_type_name = line.split('|')[-1].split('}')[0]
            elif line == ' |}':
                in_table = False
                end_i = i
                break
            elif line.startswith(' | ({{Type|') or line.startswith(' | {{Type|'):
                current_value = line[3:]
            elif line.startswith(' |'):
                current_notes = line[2:].strip()
                datas[current_type_name] = {
                    'value': current_value,
                    'notes': current_notes
                }

                current_type_name = None
                current_value = None
                current_notes = None
    return datas, start_i, end_i

def gen(parsed: dict, burger_entities_data: dict, mappings: Mappings):
    data_serializer_names = generate_metadata_names(burger_entities_data['dataserializers'], mappings)

    content = ''
    content += '{{Metadata type definition/begin}}\n'
    content += ' ! Value\n'
    content += ' ! Notes\n'
    for dataserializer_id in range(len(data_serializer_names)):
        name = data_serializer_names[dataserializer_id]
        value = parsed.get(name, {}).get('value', 'TODO')
        notes = parsed.get(name, {}).get('notes', 'TODO')

        content += f'{{{{Metadata type definition|{name}}}}}\n'
        content += f' | {value}\n'
        content += f' | {notes}\n' if notes else ' |\n'

    content += ' |}\n'
    return content