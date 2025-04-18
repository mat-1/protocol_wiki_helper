import re
from ...context import UpdateContext

from . import (
    main_entities_table,
    entity_metadata_tables,
    entity_metadata_format_table,
)


def update(ctx: UpdateContext, text: str) -> str:
    text = re.sub(
        r'(?<=Minecraft Java Edition )(\d+\.\d+\.\d+)', ctx.version, text, count=1
    )
    # and "These entity IDs are up to date for 1.20.2"
    text = re.sub(
        r'(?<=These entity IDs are up to date for )\d+\.\d+\.\d+',
        ctx.version,
        text,
        count=1,
    )

    mappings = ctx.mappings()
    burger_data = ctx.burger_data()
    burger_entities_data = burger_data[0]['entities']

    text = main_entities_table.update(text, burger_entities_data)
    text = entity_metadata_tables.update(text, burger_entities_data, mappings)
    text = entity_metadata_format_table.update(text, burger_entities_data, mappings)

    return text
