from ..context import UpdateContext


def update(ctx: UpdateContext, text: str) -> str:
    registries_report = ctx.registries_report()

    lines = text.splitlines()

    wiki_data, start_i, end_i = parse(lines)

    lines[start_i : end_i + 1] = gen_command_data(
        wiki_data, registries_report
    ).splitlines()

    return '\n'.join(lines)


def parse(lines: list[str]) -> tuple[dict, int, int]:
    start_i = None
    end_i = None

    i = -1

    # map like { 'brigadier:bool': { 'properties': '...', 'description': '...' } }
    data = {}

    def next_line():
        nonlocal i
        i += 1
        return lines[i]

    while next_line() != '=== Parsers ===':
        pass
    while next_line() != '{| class="wikitable"':
        pass
    start_i = i

    while end_i is None:
        line = next_line()
        if line.startswith(' | <code>'):
            # line looks like ` | <code>brigadier:bool</code>`
            resource_id = line.split('<code>')[1].split('</code>')[0]
            properties = next_line().split('| ', 1)[1]
            description = next_line().split('| ', 1)[1]

            found_next_line = next_line()
            if found_next_line == ' |-':
                pass
            elif found_next_line == ' |}':
                end_i = i
            else:
                raise Exception(
                    f'unexpected line when parsing command data: "{found_next_line}"'
                )

            data[resource_id] = {'properties': properties, 'description': description}

    return data, start_i, end_i


def gen_command_data(wiki_data: dict, registries_report: dict) -> str:
    registry = registries_report['minecraft:command_argument_type']['entries']

    content = ''

    content += """{| class="wikitable"
 ! Numeric ID
 ! String Identifier
 ! Properties
 ! Description
"""

    entry_ids = [None] * len(registry)
    for resource_id, entry in registry.items():
        entry_ids[entry['protocol_id']] = resource_id

    for protocol_id, resource_id in enumerate(entry_ids):
        entry_wiki_data = wiki_data.get(resource_id) or {
            'properties': 'TODO',
            'description': 'TODO',
        }
        content += ' |-\n'
        content += f' | {protocol_id}\n'
        content += f' | <code>{resource_id}</code>\n'
        content += ' | ' + entry_wiki_data['properties'].rstrip() + '\n'
        content += ' | ' + entry_wiki_data['description'].rstrip() + '\n'

    content += ' |}\n'

    return content
