def update(text: str, burger_entities_data: dict) -> str:
    lines = text.splitlines()

    parsed, start_i, end_i = parse(lines)
    new_entities_table_text = gen(parsed, burger_entities_data)
    lines[start_i : end_i + 1] = new_entities_table_text.splitlines()

    return '\n'.join(lines)


def parse(lines: list[str]) -> tuple[dict, int, int]:
    in_main_entities_table = False

    table_start_i = None
    table_end_i = None

    entry_position = 0
    entry_start_line = None
    entry_width = None
    entry_height = None

    # { magma_cube: { start_line: '|-', width: '0.5202 * size', height: '0.5202 * size' }  }
    entries = {}

    for i, line in enumerate(lines):
        if line == '{| class="wikitable"':
            in_main_entities_table = True
            table_start_i = i
            continue
        if not in_main_entities_table:
            continue

        if line == '|}':
            in_main_entities_table = False
            table_end_i = i
            break

        if line.startswith('|-'):
            entry_position = 0
            entry_start_line = line
            entry_width = None
            entry_height = None
        if entry_position == 1:
            # protocol id
            pass
        elif entry_position == 2:
            # display name
            pass
        elif entry_position == 3:
            # width
            entry_width = line[2:]
        elif entry_position == 4:
            # height
            entry_height = line[2:]
        elif entry_position == 5:
            # resource id
            entity_resource_id = line[2:].split(':')[-1].split('<')[0]
            entries[entity_resource_id] = {
                'start_line': entry_start_line,
                'width': entry_width,
                'height': entry_height,
            }

        entry_position += 1

    return (entries, table_start_i, table_end_i)


# update the main entities table
def gen(parsed_main_entities_table: dict, burger_entities_data: dict) -> str:
    content = ''

    content += """{| class="wikitable"
|- 
! Type
! Name
! bounding box x and z
! bounding box y
! ID
"""

    entities = burger_entities_data['entity'].items()
    # filter by id
    entities = filter(lambda x: 'id' in x[1], entities)
    # sort by id
    entities = sorted(entities, key=lambda x: x[1]['id'])

    for entity_resource_id, entity in entities:
        # |-
        # | 0
        # | Allay
        # | 0.35
        # | 0.6
        # | <code>minecraft:allay</code>

        # this varies for some entities like `marker`, where it'll be like `|- style="background: #ffaaaa;"` instead
        start_line = '|-'

        print(entity)

        entity_protocol_id = entity['id']
        entity_display_name = entity['display_name']
        entity_width = entity['width']
        entity_height = entity['height']

        old_entity = parsed_main_entities_table.get(entity_resource_id)
        if old_entity:
            start_line = old_entity['start_line']
            entity_width = old_entity['width']
            entity_height = old_entity['height']

        entry_content = ''
        entry_content += f'{start_line}\n'
        entry_content += f'| {entity_protocol_id}\n'
        entry_content += f'| {entity_display_name}\n'
        entry_content += f'| {entity_width}\n'
        entry_content += f'| {entity_height}\n'
        entry_content += f'| <code>minecraft:{entity_resource_id}</code>\n'

        content += entry_content

    content += '|}'
    return content
