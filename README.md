# protocol_wiki_helper

A tool for helping update certain protocol-related articles on the Minecraft Wiki to new versions. 

## Usage

```sh
uv sync
uv run python main.py <new version> <article name>
# Example: uv run python main.py 1.21.6 packets
```

After running those commands, the program will first ask you to paste the
article wikitext into a file. It'll run a few data extractors, and when it's
done it'll write the new wikitext into a different file and tell you its path.

Note that this script will *not* do everything for you. It merely provides a
less tedious starting point for you to work on updating the wiki.

For some changes, it'll generate "todo" comments for you to look at. You should
carefully look through the diff to make sure that everything was updated
correctly.

## Supported articles

- [Packets](https://minecraft.wiki/w/Java_Edition_protocol/Packets)
  - Updates the version name and protocol number at the top.
  - Removes sections for removed packets.
  - Adds placeholder sections for new packets.
  - Updates all packet IDs.
- [Entity_metadata](https://minecraft.wiki/w/Java_Edition_protocol/Entity_metadata)
  - Updates the version name.
  - Adds new entities to the Entities table, including their name, bounding box, and ID. Bounding box data for existing entities isn't updated.
  - Adds placeholders for new types in the Entity Metadata Format table.
  - Updates the metadata tables for every entity, but doesn't modify the "meaning" or "default" columns for existing entities.
- [Slot_data](https://minecraft.wiki/w/Java_Edition_protocol/Slot_data)
  - Adds placeholder entries for new data components.
  - Updates all component IDs.
  - Removes entries for removed components.
- [Command_data](https://minecraft.wiki/w/Java_Edition_protocol/Command_data)
  - Adds placeholder entries for parsers.
  - Updates all parsers IDs.
  - Removes entries for removed parsers.
