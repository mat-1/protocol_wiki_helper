# protocol_wiki_helper

A tool for helping update certain protocol-related articles on the Minecraft Wiki to new versions. 

## Usage

```sh
uv sync
uv run python main.py <new version> <article name>
# Example: uv run python main.py 1.21.5 java_edition_protocol
```

After running those commands, the program will first ask you to paste the article wikitext into a file.
When it finishes generating, it'll write the new wikitext into a different file and tell you its path.

Note that this script will *not* do everything for you.
It merely provides a less tedious starting point for you to work on updating the wiki.

It will sometimes include "todo"s for you to look at, but those will not always be generated for every protocol change.
You must also make sure to carefully look through the diff to make sure that the script did not mess up anything important.

## Supported articles

- [Java_Edition_protocol](https://minecraft.wiki/w/Java_Edition_protocol)
  - Updates the version name and protocol number at the top.
  - Removes sections for removed packets.
  - Adds placeholder sections for new packets.
  - Updates all packet IDs.
- [Entity_metadata](https://minecraft.wiki/w/Minecraft_Wiki:Projects/wiki.vg_merge/Entity_metadata)
  - Updates the version name.
  - Adds new entities to the Entities table, including their name, bounding box, and ID. Bounding box data for existing entities isn't updated.
  - Adds placeholders for new types in the Entity Metadata Format table.
  - Updates the metadata tables for every entity, but doesn't modify the "meaning" or "default" columns for existing entities.
- [Slot_Data](https://minecraft.wiki/w/Minecraft_Wiki:Projects/wiki.vg_merge/Slot_Data)
  - Adds placeholder entries for new data components.
  - Removes sections for removed components.

