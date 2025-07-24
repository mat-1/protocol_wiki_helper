import re
from ..context import UpdateContext


def update(ctx: UpdateContext, text: str) -> str:
    protocol_version_id = ctx.protocol_version()
    packets_report = ctx.packets_report()

    text = re.sub(
        r'(?<=for \[\[Minecraft Wiki:Projects/wiki\.vg merge/Protocol version numbers\|)(\d+\.\d+\.\d+), protocol (\d+)',
        f'{ctx.version}, protocol {protocol_version_id}',
        text,
        count=1,
    )

    text = re.sub(
        r'\(currently (\d+) in Minecraft (\d+\.\d+\.\d+)\)\.',
        f'(currently {protocol_version_id} in Minecraft {ctx.version}).',
        text,
        count=1,
    )

    text = re.sub(
        r'pack with version <code>(\d+\.\d+\.\d+)</code>',
        f'pack with version <code>{ctx.version}</code>',
        text,
        count=1,
    )

    lines = text.splitlines()
    parsed_packets, start_i, end_i = parse_packets(lines)
    new_packets_text = generate(parsed_packets, packets_report)

    lines[start_i:end_i] = new_packets_text.splitlines()

    return '\n'.join(lines)


def parse_packets(lines: list[str]) -> tuple[dict, int, int]:
    i = 0

    # {
    #   Status: {
    #       wikitext: "...",
    #       directions: {
    #           Clientbound: {
    #               packets: {
    #                   "Status Response": { protocol_id: 0, wikitext: "..."  }
    #              }
    #           }
    #       }
    #   }
    # }
    data = {}

    # skip ahead until we get to == Status ==
    while lines[i] != '== Status ==':
        i += 1

    start_index = i

    cur_state = None
    cur_direction = None
    cur_packet_name = None

    while i < len(lines):
        line = lines[i]
        i += 1

        if line.startswith('== '):
            if line == '== Navigation ==':
                end_index = i - 1
                break

            # state
            cur_state = line.strip('=').strip()
            cur_direction = None
            cur_packet_name = None
            data[cur_state] = {'wikitext': '', 'directions': {}}
        elif line.startswith('=== '):
            # direction
            cur_direction = line.strip('=').strip()
            cur_packet_name = None
            data[cur_state]['directions'][cur_direction] = {
                'wikitext': '',
                'packets': {},
            }
        elif line.startswith('==== '):
            # packet name
            cur_packet_name = line.strip('=').strip()
            data[cur_state]['directions'][cur_direction]['packets'][cur_packet_name] = {
                'wikitext': '',
                'protocol_id': None,
                'resource_id': None,
            }
        else:
            # cur_wikitext += line + '\n'
            if cur_state:
                container_ref = data[cur_state]
                if cur_direction:
                    container_ref = container_ref['directions'][cur_direction]
                    if cur_packet_name:
                        container_ref = container_ref['packets'][cur_packet_name]
                        # identify lines that look like  | ''protocol:''<br/><code>0x00</code><br/><br/>''resource:''<br/><code>status_response</code>
                        if line.startswith(' | ') and "''protocol:''" in line:
                            protocol_id = line.split('code>')[1].split('<')[0]
                            container_ref['protocol_id'] = int(protocol_id, 0)
                            resource_id = line.split('code>')[3].split('<')[0]
                            container_ref['resource_id'] = resource_id
                container_ref['wikitext'] += line + '\n'

    return data, start_index, end_index


def generate(wiki_data: dict, packets_report: dict) -> str:
    content = ''

    # used for identifying packets with the same name in multiple states
    resource_ids_to_states = {}
    for state_name, state_packets in packets_report.items():
        for direction_name, direction_packets in state_packets.items():
            for resource_id in direction_packets:
                if resource_id not in resource_ids_to_states:
                    resource_ids_to_states[resource_id] = set()
                resource_ids_to_states[resource_id].add(state_name)

    for state_name in wiki_data:
        wiki_state_data = wiki_data[state_name]
        content += f'== {state_name} ==\n'
        content += wiki_state_data['wikitext']
        for direction_name in wiki_state_data['directions']:
            wiki_direction_data = wiki_state_data['directions'][direction_name]
            content += f'=== {direction_name} ===\n'
            content += wiki_direction_data['wikitext']

            resource_id_to_wiki_name = {}
            for packet_name in wiki_direction_data['packets']:
                wiki_packet_data = wiki_direction_data['packets'][packet_name]
                resource_id = wiki_packet_data['resource_id']
                assert resource_id
                resource_id_to_wiki_name[resource_id] = packet_name

            vanilla_packets = packets_report[state_name.lower()][direction_name.lower()]

            # identify remove packets
            for resource_id, wiki_name in resource_id_to_wiki_name.copy().items():
                if 'minecraft:' + resource_id not in vanilla_packets:
                    print('removed packet', wiki_name)
                    wiki_direction_data['packets'].pop(wiki_name)
                    del resource_id_to_wiki_name[resource_id]

            for original_resource_id, packet_data in vanilla_packets.items():
                resource_id = original_resource_id.split(':')[1]
                if resource_id in resource_id_to_wiki_name:
                    # update the protocol id
                    wiki_name = resource_id_to_wiki_name[resource_id]
                    wiki_direction_data['packets'][wiki_name]['protocol_id'] = (
                        packet_data['protocol_id']
                    )
                else:
                    # insert into the wiki data
                    generated_wiki_name = resource_id.replace('_', ' ').title()
                    # if the resource id is present in any other states, then add the current state in parentheses
                    if len(resource_ids_to_states[original_resource_id]) > 1:
                        generated_wiki_name += f' ({state_name.lower()})'

                    wikitext = 'TODO\n\n'

                    wiki_state = state_name
                    if direction_name == 'Clientbound':
                        wiki_direction = 'Client'
                    elif direction_name == 'Serverbound':
                        wiki_direction = 'Server'
                    else:
                        raise ValueError(f'Unknown direction: {direction_name}')

                    # the protocol and resource get replaced here later
                    wikitext += f"""{{| class="wikitable"
 ! Packet ID
 ! State
 ! Bound To
 ! Field Name
 ! Field Type
 ! Notes
 |-
 | rowspan="2"| ''protocol:''<br/><code>0x00</code><br/><br/>''resource:''<br/><code>todo</code>
 | rowspan="2"| {wiki_state}
 | rowspan="2"| {wiki_direction}
 | TODO: Field name
 | {{{{Type|TODO}}}}
 | TODO: Notes
 |-
 | TODO: Field name
 | {{{{Type|TODO}}}}
 | TODO: Notes
 |}}"""

                    wiki_direction_data['packets'][generated_wiki_name] = {
                        'wikitext': wikitext,
                        'protocol_id': packet_data['protocol_id'],
                        'resource_id': resource_id,
                    }

            packets_sorted = sorted(
                wiki_direction_data['packets'].items(),
                key=lambda x: x[1]['protocol_id'],
            )
            for packet_name, wiki_packet_data in packets_sorted:
                content += f'==== {packet_name} ====\n'

                wikitext = wiki_packet_data['wikitext']

                wikitext_lines = wikitext.splitlines()
                new_wikitext_lines = []

                for line in wikitext_lines:
                    # replace the ids
                    if "''protocol:''" in line:
                        prefix = line.split("''protocol:''")[0]
                        protocol_id = wiki_packet_data['protocol_id']
                        resource_id = wiki_packet_data['resource_id']
                        # ''protocol:''<br/><code>0x00</code><br/><br/>''resource:''<br/><code>todo</code>
                        line = f"{prefix}''protocol:''<br/><code>0x{protocol_id:02X}</code><br/><br/>''resource:''<br/><code>{resource_id}</code>"

                    new_wikitext_lines.append(line)

                content += '\n' + ('\n'.join(new_wikitext_lines).strip()) + '\n\n'

    return content
