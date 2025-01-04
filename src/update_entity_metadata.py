import re
import shutil
import sys
from lib import download, extract

from entity_metadata import main_entities_table, entity_metadata_tables, entity_metadata_format_table

version_id = sys.argv[1]

mappings = download.get_mappings_for_version(version_id)
burger_data = extract.get_burger_data_for_version(version_id)

burger_entities_data = burger_data[0]['entities']

def main():
    shutil.copy('contents/entity_metadata_ORIGINAL.wikitext', 'contents/entity_metadata.wikitext')

    # regex replace the first instance of "Minecraft Java Edition a.b.c" with the version_id
    with open('contents/entity_metadata.wikitext', 'r') as f:
        contents = f.read()
    contents = re.sub(r'(?<=Minecraft Java Edition )(\d+\.\d+\.\d+)', version_id, contents, count=1)
    # and "These entity IDs are up to date for 1.20.2"
    contents = re.sub(r'(?<=These entity IDs are up to date for )\d+\.\d+\.\d+', version_id, contents, count=1)
    with open('contents/entity_metadata.wikitext', 'w') as f:
        f.write(contents)

    main_entities_table.update(burger_entities_data)
    entity_metadata_tables.update(burger_entities_data, mappings)
    entity_metadata_format_table.update(burger_entities_data, mappings)





main()
