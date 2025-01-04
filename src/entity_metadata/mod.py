from typing import Optional
import wiki_utils
from lib.mappings import Mappings


def determine_field_default(default: str, serializer: str):
    if default is None:
        # some types don't have Default implemented
        if serializer == 'CompoundTag':
            default = 'Empty'
        elif serializer == 'CatVariant':
            default = 'BLACK'
        elif serializer == 'PaintingVariant':
            default = 'KEBAB'
        elif serializer == 'FrogVariant':
            default = 'TEMPERATE'
        elif serializer == 'VillagerData':
            default = 'Plains/None/1'
        elif serializer == 'VillagerData':
            default = 'Plains/None/1'
        elif serializer == 'Slot':
            default = 'Empty'
        else:
            default = 'TODO'
    else:
        if serializer == 'Boolean':
            default = 'true' if default else 'false'

    return default


def generate_metadata_names(burger_dataserializers: dict, mappings: Mappings):
    serializer_names: list[Optional[str]] = [None] * len(burger_dataserializers)
    for burger_serializer in burger_dataserializers.values():
        print(burger_serializer)

        # burger gives us the wrong class, so we do this instead
        data_serializers_class = mappings.get_class_from_deobfuscated_name('net.minecraft.network.syncher.EntityDataSerializers')
        mojmap_name = mappings.get_field(data_serializers_class, burger_serializer['field']).lower()

        # mojmap names : wiki names
        name_mappings = {
            'int': 'VarInt',
            'long': 'VarLong',
            'component': 'Text Component',
            'optional_component': 'Optional Text Component',
            'item_stack': 'Slot',
            'optional_uuid': 'Optional UUID',
            'block_pos': 'Position',
            'optional_block_pos': 'Optional Position',
            'optional_global_pos': 'Optional Global Position',
            'compound_tag': 'NBT',
            'optional_unsigned_int': 'Optional VarInt',
            'vec3': 'Vector3'
        }

        serializer_names[burger_serializer['id']] = name_mappings.get(mojmap_name) or mojmap_name.replace('_', ' ').title()
    return serializer_names

def read_text() -> str:
    return wiki_utils.read_article('entity_metadata')

def replace_lines(new_text: list[str] | str, start: int, end: int):
    return wiki_utils.replace_article_lines('entity_metadata', new_text, start, end)


