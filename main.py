import argparse
import os
import re
import sys

from src.context import UpdateContext
import src.updaters.entity_metadata as entity_metadata
import src.updaters.java_edition_protocol as java_edition_protocol
import src.updaters.slot_data as slot_data

UPDATERS = {
    'entity_metadata': entity_metadata,
    'java_edition_protocol': java_edition_protocol,
    'slot_data': slot_data,
}

BOLD = '\033[1m'
RESET = '\033[m'
GRAY = '\033[90m'
GREEN = '\033[92m'

if os.environ.get('NO_COLOR'):
    BOLD = ''
    RESET = ''
    GRAY = ''


def main():
    parser = argparse.ArgumentParser(
        prog='protocol_wiki_helper',
        description='A tool for helping update pages on the Minecraft Wiki protocol pages.',
    )

    parser.add_argument(
        'version',
        help='The Minecraft version to update to.',
    )
    parser.add_argument(
        'article',
        help='The title of wiki article to update.',
    )

    try:
        args = parser.parse_args()
    except argparse.ArgumentError as e:
        sys.stderr.write(str(e))
        sys.exit(1)

    version = args.version
    article_name = args.article.lower()

    if re.match(r'^[a-zA-Z0-9_]+$', article_name) is None:
        sys.stderr.write(f'Invalid article name "{article_name}".\n')
        sys.exit(1)

    if article_name not in UPDATERS:
        sys.stderr.write(
            f'No updater implemented for "{article_name}". Available updaters: {", ".join(UPDATERS.keys())}.\n'
        )
        sys.exit(1)
    updater = UPDATERS[article_name]

    ctx = UpdateContext(version)

    # ensure articles/{}.wikitext exists
    article_path = f'articles/{article_name}.wikitext'
    new_article_path = f'articles/{article_name}.new.wikitext'

    article_path = os.path.abspath(article_path)
    new_article_path = os.path.abspath(new_article_path)

    # create an empty file if it doesn't exist
    if not os.path.exists(article_path):
        os.makedirs(os.path.dirname(article_path), exist_ok=True)
        with open(article_path, 'w') as f:
            f.write('')

    input(
        f'Please paste article wikitext into {BOLD}{article_path}{RESET} and then press enter.\n'
    )

    article_text = open(article_path, 'r').read()
    new_article_text = updater.update(ctx, article_text)

    # make sure there's a trailing newline
    if not new_article_text.endswith('\n'):
        new_article_text += '\n'
    with open(new_article_path, 'w') as f:
        f.write(new_article_text)

    print(f'{GREEN}Updated article written to {BOLD}{new_article_path}{RESET}')
    print(
        f"""{GRAY}Hint: Run the following command to show a diff:
$ diff --color=always {article_path} {new_article_path} | less"""
    )


if __name__ == '__main__':
    main()
