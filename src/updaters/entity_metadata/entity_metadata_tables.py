from ...datagen.mappings import Mappings
from ...datagen.utils import to_snake_case
from .util import (
    determine_field_default,
    generate_metadata_names,
)


def update(text: str, burger_entities_data: dict, mappings: Mappings) -> str:
    lines = text.splitlines()
    parsed, start_i, end_i = parse(lines)
    new_metadata_table_text = gen(parsed, burger_entities_data, mappings)

    lines[start_i + 2 : end_i] = new_metadata_table_text.splitlines()

    return '\n'.join(lines)


def parse(lines: list[str]) -> tuple[list, int, int]:
    in_entity_metadata_section = False
    is_before_table = True
    is_after_table = False

    in_bit_mask = False
    current_mask = None

    section_start_i = None

    # this is constant, the last 3 lines are reserved for the copyright disclaimer and stuff
    section_end_i = -3

    entry_display_name = None
    entry_data = {}

    # { 'Entity': {
    #   extends: None,
    #   wikitext_before: 'The base class.',
    #   wikitext_after: 'safgsdfg',
    #   metadata: [
    #     {
    #       meaning: { 1: 'Is on fire' },
    #       default: '0',
    #     },
    #     {
    #       meaning: 'Air ticks',
    #       default: '300',
    #     },
    #   ]
    # } }
    entries = {}

    # { meaning: 'Air ticks', default: '300' }
    current_metadata_field = {}

    def finish_entry():
        nonlocal entry_display_name, entry_data, is_before_table, is_after_table

        finish_field()

        if entry_display_name:
            entry_data['wikitext_before'] = entry_data.get(
                'wikitext_before', ''
            ).strip()
            entry_data['wikitext_after'] = entry_data.get('wikitext_after', '').strip()

            if 'No additional metadata.' in entry_data['wikitext_before']:
                assert 'metadata' not in entry_data
                entry_data['wikitext_before'] = (
                    entry_data['wikitext_before']
                    .replace('No additional metadata.', '')
                    .strip()
                )
                entry_data['metadata'] = []

            entries[entry_display_name] = entry_data
            print('finished entry', '"' + entry_display_name + '"', entry_data)

        entry_display_name = None
        entry_data = {}

        is_before_table = True
        is_after_table = False

    def finish_field():
        nonlocal current_metadata_field, in_bit_mask, current_mask, entry_data

        if current_metadata_field == {}:
            return

        current_metadata_field['default'] = current_metadata_field['default'].strip()

        in_bit_mask = False
        current_mask = None
        if 'metadata' not in entry_data:
            entry_data['metadata'] = []
        entry_data['metadata'].append(current_metadata_field)
        current_metadata_field = {}

    if section_end_i < 0:
        section_end_i = len(lines) + section_end_i

    for i, line in enumerate(lines[:section_end_i]):
        print(line)
        if line == '== Entity Metadata ==':
            in_entity_metadata_section = True
            section_start_i = i
            continue
        if not in_entity_metadata_section:
            continue

        if line.startswith('=== '):
            # start of a new entity
            finish_entry()
            entry_display_name = line.strip('=').strip()
            continue

        if line.lower().startswith('{{metadata inherit|'):
            # {{Metadata inherit|Fireball|inherits=Entity}}
            line = line[2:-2]
            parts = line.split('|')

            # we don't set the entry_display_name here because it might be incorrect
            assert entry_display_name

            if len(parts) > 2:
                assert parts[2].startswith('inherits=')
                extends = parts[2][len('inherits=') :]
                entry_data['extends'] = extends
            else:
                extends = None
                entry_data['extends'] = None

            assert is_before_table
            assert not is_after_table
            continue

        assert not (is_before_table and is_after_table)

        if is_before_table:
            if line.strip() == '{| class="wikitable"':
                is_before_table = False
                print('entered table')
                continue
            if 'wikitext_before' not in entry_data:
                entry_data['wikitext_before'] = ''
            entry_data['wikitext_before'] += line + '\n'
        if is_after_table:
            if 'wikitext_after' not in entry_data:
                entry_data['wikitext_after'] = ''
            entry_data['wikitext_after'] += line + '\n'

        if not is_before_table and not is_after_table:
            # in table
            if line.startswith(' ! Bit mask') or line == ' |colspan="2"| Flags':
                # entering bit mask
                in_bit_mask = True
                new_meaning = {}
                if 'meaning' in current_metadata_field:
                    # rarely an element can have a meaning and a bitmask (like Living Entity)
                    new_meaning['main'] = current_metadata_field['meaning']
                current_metadata_field['meaning'] = new_meaning
                print('ok, entering bit mask')
            elif line.strip() == '|}':
                # leaving table
                is_after_table = True
                continue
            elif '{{Metadata id|}}' in line:
                # start of new field
                finish_field()
                continue
            if line.startswith(' |rowspan="') or line.startswith(' | rowspan="'):
                # default for a bit mask. rarely this can exist outside of
                # is_bit_mask like for Living Entity
                current_metadata_field['default'] = line.split('| ')[-1]
                print('parsed default for bit mask', current_metadata_field['default'])
            elif in_bit_mask:
                if line.startswith(' | 0x'):
                    current_mask = line.split(' | ')[1]
                    if ' || ' in line:
                        # some bitfields have the `meaning` separated by a || instead of being on a different line
                        current_mask, meaning = current_mask.split(' || ', 1)
                    # the int(x, 0) makes it able to parse hex
                    current_mask = int(current_mask, 0)
                    if ' || ' in line:
                        current_metadata_field['meaning'][current_mask] = meaning
                elif line.startswith(' | '):
                    if current_mask is None:
                        continue
                    meaning = line.split(' | ')[1]
                    if current_mask not in current_metadata_field['meaning']:
                        current_metadata_field['meaning'][current_mask] = ''
                    current_metadata_field['meaning'][current_mask] += meaning
                elif not line.startswith(' |'):
                    if current_mask is not None:
                        current_metadata_field['meaning'][current_mask] += '\n' + line
            else:
                if line.replace(' ', '').startswith('|colspan="2"|'):
                    # `meaning` lines start with this
                    current_metadata_field['meaning'] = line.split('|', 2)[-1].strip()
                    print('parsed meaning', current_metadata_field['meaning'])
                elif (
                    not line.startswith(' | {{')
                    and 'meaning' in current_metadata_field
                    and 'default' not in current_metadata_field
                    and not line.startswith(' | ')
                ):
                    # must be a multiline meaning
                    current_metadata_field['meaning'] += '\n' + line
                elif (
                    not line.startswith(' | {{')
                    and 'meaning' in current_metadata_field
                    and line.startswith(' | ')
                ):
                    # if it doesn't match that, then it must be a `default`
                    print('parsed default', line[len(' | ') :])
                    if 'default' not in current_metadata_field:
                        current_metadata_field['default'] = ''
                    current_metadata_field['default'] += line[len(' | ') :] + '\n'

    finish_entry()

    return (entries, section_start_i, section_end_i)


def gen(
    parsed_entity_metadata_tables: list, burger_entities_data: dict, mappings: Mappings
) -> str:
    content = ''

    entities_map = burger_entities_data['entity']
    entity_resource_ids_partially_sorted = list(entities_map.keys())
    # sort by name first
    entity_resource_ids_partially_sorted.sort()
    # then sort by id (and put the abstract entities last - they have no id)
    entity_resource_ids_partially_sorted.sort(
        key=lambda x: entities_map[x].get('id', 999999)
    )

    entity_resource_ids_organized = ['~abstract_entity']

    # recursively sort them so entities are always immediately after their parents
    def traverse(parent: str):
        for entity_resource_id in entity_resource_ids_partially_sorted:
            if entity_resource_id == '~abstract_entity':
                continue
            entity = entities_map[entity_resource_id]
            extends = entity['metadata'][0]['entity']
            if extends == parent:
                entity_resource_ids_organized.append(entity_resource_id)
                traverse(entity_resource_id)

    traverse('~abstract_entity')

    data_serializer_names = generate_metadata_names(
        burger_entities_data['dataserializers'], mappings
    )

    content = ''
    for entity_resource_id in entity_resource_ids_organized:
        print('-')
        entity = entities_map[entity_resource_id]
        print(entity_resource_id)
        entity_name_map = {
            # if the wiki name starts with "Abstract ", it doesn't need to go here
            '~abstract_entity': 'Entity',
            '~abstract_living': 'Living Entity',
            '~abstract_insentient': 'Mob',
            '~abstract_creature': 'Creature',
            '~abstract_ageable': 'Ageable Mob',
            '~abstract_animal': 'Animal',
            '~abstract_tameable': 'Tameable Animal',
            '~abstract_monster': 'Monster',
            '~abstract_display': 'Display',
            '~abstract_boat': 'Boat',
            '~abstract_thrown_item_projectile': 'Thrown Item Projectile',
            '~abstract_raider': 'Raider',
            '~abstract_spellcaster_illager': 'Spellcaster Illager',
            '~abstract_chested_horse': 'Chested Horse',
            '~abstract_vehicle': 'Abstract Vehicle',
            '~abstract_piglin': 'Base Piglin',
            # # incorrect Minecraft Wiki names go here, they'll get replaced by
            # # the correct en_us.json names
            # 'experience_bottle': 'Thrown Experience Bottle',
            # 'item': 'Item Entity',
            # 'glow_item_frame': 'Glowing Item Frame',
            # 'potion': 'Thrown Potion',
            # 'tnt': 'Primed Tnt',
            # 'trident': 'Thrown Trident',
            # 'fishing_bobber': 'Fishing Hook',
            # 'tropical_fish': 'Tropical fish',
            # 'chest_minecart': 'Minecart Chest',
            # 'command_block_minecart': 'Minecart Command Block',
            # 'furnace_minecart': 'Minecart Furnace',
            # 'hopper_minecart': 'Minecart Hopper',
            # 'spawner_minecart': 'Minecart Spawner',
            # 'tnt_minecart': 'Minecart TNT',
            # '~abstract_fish': 'Abstract fish',
            # 'pufferfish': 'Puffer fish'
        }

        def get_name_from_map(resource_id):
            new_name = entity_name_map.get(resource_id)
            if new_name:
                return new_name
            if resource_id.startswith('~abstract_'):
                return resource_id[1:].replace('_', ' ').title()
            return None

        entity_old_wiki_name = (
            get_name_from_map(entity_resource_id) or entity['display_name']
        )
        entity_display_name = entity.get('display_name') or get_name_from_map(
            entity_resource_id
        )

        assert entity_old_wiki_name is not None
        assert entity_display_name is not None

        wiki_entity = parsed_entity_metadata_tables.get(entity_old_wiki_name)

        print(entity_old_wiki_name, entity_display_name, wiki_entity)
        # if entity_resource_id not in {
        #     'bamboo_chest_raft', 'bamboo_raft', 'breeze_wind_charge', 'experience_orb',
        #     'leash_knot', 'lightning_bolt', 'marker', 'ominous_item_spawner', 'shulker_bullet',
        #     'wind_charge', 'magma_cube', '~abstract_creature', 'allay', 'pufferfish', 'glow_squid',
        #     'armadillo', 'bogged', 'breeze', 'creaking', 'cave_spider',
        # } and not entity_resource_id.endswith('_boat'):
        #     assert wiki_entity is not None

        if entity_resource_id == '~abstract_entity':
            entity_inherits = None
            entity_metadata = entity['metadata'][-1]
        else:
            # the list is of all the parents and then the entity itself
            entity_inherits = entity['metadata'][0]['entity']
            entity_metadata = (
                entity['metadata'][-1] if len(entity['metadata']) > 1 else None
            )
        print('inherits', entity_inherits)

        # === Interaction ===
        content += f'=== {entity_display_name} ===\n'
        content += '\n'
        if entity_inherits:
            entity_inherits_display_name = entities_map[entity_inherits].get(
                'display_name'
            ) or get_name_from_map(entity_inherits)
            content += f'{{{{Metadata inherit|{entity_display_name}|inherits={entity_inherits_display_name}}}}}\n'
        else:
            content += f'{{{{Metadata inherit|{entity_display_name}}}}}\n'
        content += '\n'

        if wiki_entity and wiki_entity['wikitext_before']:
            content += f'{wiki_entity["wikitext_before"]}\n'
            content += '\n'

        if not entity_metadata:
            content += 'No additional metadata.\n'
            content += '\n'
            continue

        content += '{| class="wikitable"\n'
        content += ' ! Index\n'
        content += ' ! Type\n'
        content += ' !style="width: 250px;" colspan="2"| Meaning\n'
        content += ' ! Default\n'

        print('entity_metadata', entity_metadata)

        # determine the location of the bitfield, if any
        known_bitfield_field_index = None
        # if the wiki considers something to be a bitfield, then it is
        if wiki_entity:
            for i, metadata_field in enumerate(wiki_entity['metadata']):
                if isinstance(metadata_field['meaning'], dict):
                    known_bitfield_field_index = i
                    break
        # otherwise, try to guess which field it is
        if known_bitfield_field_index is None:
            if entity_metadata['bitfields'] != []:
                # guess that it's the first `byte` field
                if known_bitfield_field_index is None:
                    for i, metadata_field in enumerate(entity_metadata['data']):
                        if metadata_field['serializer'] == 'Byte':
                            known_bitfield_field_index = i
                            break
                assert known_bitfield_field_index is not None

        for i, metadata_field in enumerate(entity_metadata['data']):
            print(i, metadata_field)
            wiki_metadata_field = None
            if wiki_entity:
                try:
                    wiki_metadata_field = wiki_entity['metadata'][i]
                except IndexError:
                    pass
                print('  wiki_metadata_field', wiki_metadata_field)

            mojmap_field_name = mappings.get_field(
                entity_metadata['class'], metadata_field['field']
            )

            cleaned_mojmap_field_name = mojmap_field_name
            if cleaned_mojmap_field_name.startswith('DATA_ID_'):
                cleaned_mojmap_field_name = cleaned_mojmap_field_name[len('DATA_ID_') :]
            elif cleaned_mojmap_field_name.startswith('DATA_'):
                cleaned_mojmap_field_name = cleaned_mojmap_field_name[len('DATA_') :]
            cleaned_mojmap_field_name = cleaned_mojmap_field_name.replace(
                '_', ' '
            ).lower()
            # upper first letter
            cleaned_mojmap_field_name = (
                cleaned_mojmap_field_name[0].upper() + cleaned_mojmap_field_name[1:]
            )

            metadata_field_type = data_serializer_names[metadata_field['serializer_id']]
            metadata_field_meaning = (
                wiki_metadata_field['meaning']
                if wiki_metadata_field
                else f'TODO: {cleaned_mojmap_field_name}'
            )
            metadata_field_default = (
                wiki_metadata_field['default']
                if wiki_metadata_field
                else determine_field_default(
                    metadata_field.get('default'), metadata_field_type
                )
            )

            # |-
            # | {{Metadata id|}}
            # | {{Metadata type|Position}}
            # |colspan="2"| Home pos
            # | (0, 0, 0)
            content += ' |-\n'
            if known_bitfield_field_index == i:
                bitfields = entity_metadata['bitfields']
                wiki_bitfields = (
                    wiki_metadata_field['meaning']
                    if (
                        wiki_metadata_field
                        and isinstance(wiki_metadata_field['meaning'], dict)
                    )
                    else None
                )

                main_bitfield_meaning = (
                    wiki_bitfields.get('main') if wiki_bitfields else None
                )
                if main_bitfield_meaning:
                    del wiki_bitfields['main']

                if bitfields == []:
                    # must be a field that's only considered a bitfield by the wiki, so fill the list with whatever the wiki says
                    for mask, _meaning in wiki_bitfields.items():
                        bitfields.append({'mask': int(mask)})

                skip_filling_unused = False

                # hardcoded fixes for some entities
                if entity_resource_id == '~abstract_horse':
                    # is mouth open
                    bitfields.append({'mask': 0x40})
                if entity_resource_id == 'sheep':
                    # Color ID
                    bitfields.append({'mask': 0x0F})
                    skip_filling_unused = True

                if not skip_filling_unused:
                    # add the missing bitfield masks
                    current_mask = 1
                    print('bitfields', bitfields)
                    print('wiki_bitfields', wiki_bitfields)
                    highest_mask = max(bitfield['mask'] for bitfield in bitfields)
                    old_bitfield_masks = set(bitfield['mask'] for bitfield in bitfields)
                    while current_mask <= highest_mask:
                        if current_mask not in old_bitfield_masks:
                            bitfields.append({'mask': current_mask})
                        current_mask *= 2

                bitfields_rowspan = len(bitfields) + 1
                if main_bitfield_meaning:
                    bitfields_rowspan += 1
                content += f' |rowspan="{bitfields_rowspan}"| {{{{Metadata id|}}}}\n'
                content += f' |rowspan="{bitfields_rowspan}"| {{{{Metadata type|{metadata_field_type}}}}}\n'
                if main_bitfield_meaning:
                    content += f' |colspan="2"| {main_bitfield_meaning}\n'
                    content += (
                        f' |rowspan="{bitfields_rowspan}"| {metadata_field_default}\n'
                    )
                    content += ' |-\n'
                    content += ' ! Bit mask\n'
                    content += ' ! Meaning\n'
                else:
                    content += ' ! Bit mask\n'
                    content += ' ! Meaning\n'
                    content += (
                        f' |rowspan="{bitfields_rowspan}"| {metadata_field_default}\n'
                    )

                # sort bitfields by mask
                for bitfield in sorted(bitfields, key=lambda x: x['mask']):
                    print('bitfield', bitfield)
                    bitfield_mojmap_field_name = (
                        mappings.get_method(
                            bitfield.get('class') or entity_metadata['class'],
                            bitfield['method'],
                            '',
                        )
                        if 'method' in bitfield
                        else None
                    )
                    if bitfield_mojmap_field_name:
                        cleaned_bitfield_mojmap_field_name = to_snake_case(
                            bitfield_mojmap_field_name
                        )
                        cleaned_bitfield_mojmap_field_name = (
                            cleaned_bitfield_mojmap_field_name.replace('_', ' ').lower()
                        )
                    else:
                        cleaned_bitfield_mojmap_field_name = None

                    bitfield_meaning = (
                        wiki_bitfields.get(bitfield['mask'], "''Unused''")
                        if wiki_bitfields
                        else f'bitfield TODO: {cleaned_bitfield_mojmap_field_name}'
                    )

                    content += ' |-\n'
                    content += f' | 0x{bitfield["mask"]:02X}\n'
                    content += f' | {bitfield_meaning}\n'
            else:
                content += ' | {{Metadata id|}}\n'
                content += f' | {{{{Metadata type|{metadata_field_type}}}}}\n'
                content += f' |colspan="2"| {metadata_field_meaning}\n'
                content += f' | {metadata_field_default}\n'

        content += '|}\n'
        content += '\n'

        if wiki_entity and wiki_entity['wikitext_after']:
            content += f'{wiki_entity["wikitext_after"]}\n'
            content += '\n'

    return content
