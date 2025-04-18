# protocol_wiki_helper

Some messy code to help with editing certain protocol-related Minecraft Wiki pages.

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
- [Entity_metadata](https://minecraft.wiki/w/Minecraft_Wiki:Projects/wiki.vg_merge/Entity_metadata)
- [Slot_data](https://minecraft.wiki/w/Minecraft_Wiki:Projects/wiki.vg_merge/Slot_Data)
