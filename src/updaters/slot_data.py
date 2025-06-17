from ..context import UpdateContext


def update(ctx: UpdateContext, text: str) -> str:
    registries_report = ctx.registries_report()

    lines = text.splitlines()

    wiki_data, start_i, end_i = parse(lines)

    lines[start_i : end_i + 1] = gen_slot_data(
        wiki_data, registries_report
    ).splitlines()

    return '\n'.join(lines)


def parse(lines: list[str]) -> tuple[dict, int, int]:
    start_i = None
    end_i = None

    i = -1

    # map of like { 'minecraft:custom_data': 'Customizable data that doesn't fit any specific component.\n | As follows: ...' }
    data = {}

    def next_line():
        nonlocal i
        i += 1
        return lines[i]

    while next_line() != '= Structured components =':
        pass
    while next_line() != '{| class="wikitable"':
        pass
    start_i = i

    table_depth = 1

    while end_i is None:
        line = next_line()
        if line.startswith(' | <code>'):
            # line looks like ` | <code>minecraft:custom_data</code>`
            resource_id = line.split('<code>')[1].split('</code>')[0]
            description = ''

            while True:
                line = next_line()
                if line.strip().startswith('{|'):
                    table_depth += 1
                if line.strip() == '|-' and table_depth == 1:
                    break
                elif line.strip() == '|}':
                    table_depth -= 1
                    if table_depth == 0:
                        end_i = i
                        break
                description += line + '\n'
            data[resource_id] = description

    return data, start_i, end_i


def gen_slot_data(wiki_data: dict, registries_report: dict) -> str:
    registry = registries_report['minecraft:data_component_type']['entries']

    content = ''

    content += """{| class="wikitable"
 ! Type
 ! Name
 ! Description
 ! style="width: 50%" | Data
"""

    entry_ids = [None] * len(registry)
    for resource_id, entry in registry.items():
        entry_ids[entry['protocol_id']] = resource_id

    for protocol_id, resource_id in enumerate(entry_ids):
        content += ' |-\n'
        content += f' | {protocol_id}\n'
        content += f' | <code>{resource_id}</code>\n'
        description = (
            wiki_data.get(resource_id)
            or """ | TODO
 | As follows:
   {| class="wikitable"
    ! Name
    ! Type
    ! Description
    |-
    | TODO
    | {{Type|TODO}}
    | TODO
    |}
"""
        )
        content += description.rstrip() + '\n'

    content += ' |}\n'

    return content
