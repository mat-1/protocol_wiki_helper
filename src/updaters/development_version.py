import re
from ..context import UpdateContext

OTHER_REQUIRED_ARTICLES = ('java_edition_protocol', 'entity_metadata', 'slot_data')


def update(
    ctx: UpdateContext,
    text: str,
    java_edition_protocol: str,
    entity_metadata: str,
    slot_data: str,
) -> str:
    raise NotImplementedError()

    current_release_version, current_release_protocol_id = (
        extract_version_name_and_number(java_edition_protocol)
    )

    lines = text.splitlines()
    first_line = lines[0]
    if current_release_version == ctx.version:
        return RESET_CONTENT
    else:
        version_type = (
            'development version' if ctx.protocol_version() > 0x40000000 else 'release'
        )
        first_line = (
            f'This page documents the changes from release {current_release_version} (protocol {current_release_protocol_id}) '
            f'to the current {version_type} ({ctx.version}, protocol {ctx.protocol_version()}).'
        )
    lines[0] = first_line

    old_packet_names_to_ids = {}
    # identify the lines that look something like this:
    # rowspan="8"| ''protocol:''<br/><code>0x25</code><br/><br/>''resource:''<br/><code>initialize_border</code>
    cur_state = None
    cur_direction = None
    cur_name = None
    for line in java_edition_protocol.splitlines():
        if line.startswith('== '):
            cur_state = line.split('==')[1].strip()
        elif line.startswith('=== '):
            cur_direction = line.split('===')[1].strip()
        elif line.startswith('==== '):
            cur_name = line.split('====')[1].strip()
        elif "'protocol:''" in line and "''resource:''" in line:
            assert cur_name is not None

            if cur_state not in old_packet_names_to_ids:
                old_packet_names_to_ids[cur_state] = {}
            if cur_direction not in old_packet_names_to_ids[cur_state]:
                old_packet_names_to_ids[cur_state][cur_direction] = {}

            protocol_id = int(line.split('<code>')[1].split('<')[0], 0)
            resource_id = line.split('<code>')[2].split('<')[0]
            old_packet_names_to_ids[cur_state][cur_direction][cur_name] = (
                protocol_id,
                resource_id,
            )

            cur_name = None

    new_packet_resource_names_to_ids = {}
    packets_report = ctx.packets_report()
    for state in packets_report:
        if state == 'handshake':
            wiki_state = 'Handshaking'
        else:
            wiki_state = state.title()

        new_packet_resource_names_to_ids[wiki_state] = {}
        for direction in packets_report[state]:
            wiki_direction = direction.title()
            new_packet_resource_names_to_ids[wiki_state][wiki_direction] = {}
            for resource_id, packet in packets_report[state][direction].items():
                wiki_resource_id = resource_id.split(':')[1]
                protocol_id = packet['protocol_id']
                new_packet_resource_names_to_ids[wiki_state][wiki_direction][
                    wiki_resource_id
                ] = protocol_id

    # entries are tuples like ('Play', 'Clientbound', 'container_close')
    modified_packets = set()
    cur_state = None
    cur_direction = None
    for line_index, line in enumerate(list(lines)):
        if line.startswith('== '):
            cur_state = line.split('==')[1].strip()
            if cur_state == 'Handshake':
                # the wiki calls the state Handshaking because there's already a packet called Handshake
                cur_state = 'Handshaking'
        elif line.startswith('=== '):
            cur_direction = line.split('===')[1].strip()
        elif "'protocol:''" in line and "''resource:''" in line:
            resource_id = line.split('<code>')[2].split('<')[0]
            modified_packets.add((cur_state, cur_direction, resource_id))

            protocol_id = new_packet_resource_names_to_ids[cur_state][cur_direction][
                resource_id
            ]
            # rewrite the line to update the protocol id just in case
            new_line = re.sub(
                r"(?<=''protocol:''<br/><code>)0x[0-9a-fA-F]+(?=</code>)",
                hex(protocol_id),
                line,
            )
            lines[line_index] = new_line

    # formatted the same as modified_packets, tuples like ('Play', 'Clientbound', 'container_close')
    new_packets = set()
    for state in new_packet_resource_names_to_ids:
        for direction in new_packet_resource_names_to_ids[state]:
            for resource_id in new_packet_resource_names_to_ids[state][direction]:
                if resource_id not in old_packet_names_to_ids[state][direction]:
                    new_packets.add((state, direction, resource_id))

    removed_packets = set()
    for state in old_packet_names_to_ids:
        for direction in old_packet_names_to_ids[state]:
            for resource_id in old_packet_names_to_ids[state][direction]:
                if (
                    resource_id
                    not in new_packet_resource_names_to_ids[state][direction]
                ):
                    removed_packets.add((state, direction, resource_id))

    # update the Packets table
    if len(modified_packets) > 0 or len(new_packets) > 0 or len(removed_packets) > 0:
        packets_table_index = None
        for line_index, line in enumerate(list(lines)):
            if line == '=== Packets ===':
                packets_table_index = line_index + 2
                if not lines[line_index + 2].startswith('{|'):
                    # insert an empty table
                    EMPTY_TABLE_CONTENTS = [
                        '{| class="wikitable"',
                        ' ! ID',
                        ' ! Packet name',
                        ' !colspan="2"| Documentation',
                        ' |}',
                    ]
                    lines[line_index + 2 : line_index + 3] = EMPTY_TABLE_CONTENTS
                break

        new_or_updated_packets = set()
        new_or_updated_packets.update(modified_packets)
        new_or_updated_packets.update(new_packets)

    print(new_packets)

    return '\n'.join(lines)


def extract_version_name_and_number(
    java_edition_protocol: str,
) -> tuple[str, str]:
    # match regex for `Protocol version numbers|1.21.5, protocol 770]].`
    current_release_version_match = re.search(
        r'(?<=Protocol version numbers\|)(\d+\.\d+(?:\.\d+)?), protocol (\d+)',
        java_edition_protocol,
    )
    current_release_version = current_release_version_match.group(1)
    current_release_protocol_id = current_release_version_match.group(2)

    return current_release_version, current_release_protocol_id


RESET_CONTENT = """There are currently no development versions available to document on this page. For the latest stable Minecraft release, see the [[Java Edition protocol|protocol]] page. For previous development version pages, see the [[Minecraft Wiki:Projects/wiki.vg merge/Protocol version numbers|Protocol version numbers]] page.

One who wishes to commandeer the merging of this into [[Java Edition protocol|''Java Edition'' protocol]] when an update is made must be sure to respect any changes that may have occurred to the respective packets there.

== Contents ==

<div style="float:right;">__TOC__</div>

=== Data types ===

No changes so far.

=== Packets ===

No changes so far.

[[Category:Java Edition protocol]]
{{license wiki.vg}}
"""
