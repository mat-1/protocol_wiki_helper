import shutil
import sys
from lib import download, extract
from wiki_utils import read_article
import wiki_utils


version_id = sys.argv[1]

mappings = download.get_mappings_for_version(version_id)
burger_data = extract.get_burger_data_for_version(version_id)

registries = extract.get_registries_report(version_id)


def main():
    shutil.copy('contents/slot_data_ORIGINAL.wikitext', 'contents/slot_data.wikitext')

    text = read_article('slot_data')
    data, start_i, end_i = parse(text)
    new_text = gen(data)
    wiki_utils.replace_article_lines('slot_data', new_text, start_i, end_i + 1)


def parse(text: str) -> tuple[dict, int, int]:
    start_i = None
    end_i = None

    i = -1
    lines = text.splitlines()

    # map of like { 'minecraft:custom_data': 'Customizable data that doesn't fit any specific component.\n | As follows: ...' }
    data = {}

    def next_line():
        nonlocal i
        i += 1
        return lines[i]

    while next_line() != '== Structured components ==':
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
                if line == ' |-':
                    break
                elif line.strip() == '|}':
                    table_depth -= 1
                    if table_depth == 0:
                        end_i = i
                        break
                description += line + '\n'
            print(resource_id)
            data[resource_id] = description

    return data, start_i, end_i

def gen(wiki_data: dict):
    registry = registries['minecraft:data_component_type']['entries']

    content = ''

    content += '''{| class="wikitable"
 ! Type
 ! Name
 ! Description
 ! style="width: 50%" | Data
'''

    entry_ids = [None] * len(registry)
    for resource_id, entry in registry.items():
        entry_ids[entry['protocol_id']] = resource_id

    for protocol_id, resource_id in enumerate(entry_ids):
        content += f' |-\n'
        content += f' | {protocol_id}\n'
        content += f' | <code>{resource_id}</code>\n'
        description = wiki_data.get(resource_id) or ''' | TODO
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
'''
        content += description.rstrip() + '\n'

    content += ' |}\n'        

    return content



main()