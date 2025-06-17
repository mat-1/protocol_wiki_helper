import argparse
import os
import re
import sys

from src.context import UpdateContext

from src.updaters import (
    entity_metadata,
    java_edition_protocol,
    slot_data,
    development_version,
    command_data,
)

UPDATERS = {
    'entity_metadata': entity_metadata,
    'java_edition_protocol': java_edition_protocol,
    'slot_data': slot_data,
    'development_version': development_version,
    'command_data': command_data,
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
        description='A tool for helping update certain protocol-related articles on the Minecraft Wiki.',
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
    article_name = args.article.lower().replace(' ', '_')

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

    article_path, new_article_path = get_article_old_and_new_path_pair(article_name)

    other_required_articles = []
    try:
        other_required_articles = updater.OTHER_REQUIRED_ARTICLES
    except AttributeError:
        pass

    if len(other_required_articles) == 0:
        article_text = prompt_pasting_article(article_name)
        new_article_text = updater.update(ctx, article_text)
    else:
        article_names = (article_name,) + tuple(other_required_articles)
        article_texts = prompt_pasting_articles(article_names)
        new_article_text = updater.update(ctx, *article_texts)

    # make sure there's a trailing newline
    if not new_article_text.endswith('\n'):
        new_article_text += '\n'
    with open(new_article_path, 'w') as f:
        f.write(new_article_text)

    print(
        f'{GREEN}Updated article written to {BOLD}{escape_spaces_in_path(new_article_path)}{RESET}'
    )
    print(
        f"""{GRAY}Hint: Run the following command to show a diff:
$ diff --color=always {escape_spaces_in_path(article_path)} {escape_spaces_in_path(new_article_path)} | less"""
    )


def get_article_old_and_new_path_pair(article_name: str) -> tuple[str, str]:
    article_path = f'articles/{article_name}.wikitext'
    new_article_path = f'articles/{article_name}.new.wikitext'

    article_path = os.path.abspath(article_path)
    new_article_path = os.path.abspath(new_article_path)

    return article_path, new_article_path


def prompt_pasting_article(article_name: str) -> str:
    article_path, _ = get_article_old_and_new_path_pair(article_name)
    create_empty_file_if_not_exists(article_path)
    input(
        f'Please paste article wikitext into {BOLD}{escape_spaces_in_path(article_path)}{RESET} and then press enter.\n'
    )
    return open(article_path, 'r').read()


def prompt_pasting_articles(article_names: tuple[str]) -> tuple[str]:
    article_paths = []
    for name in article_names:
        article_path, _ = get_article_old_and_new_path_pair(name)
        create_empty_file_if_not_exists(article_path)
        article_paths.append(article_path)

    print(
        'Please paste the wikitext of the articles into the following paths and then press enter:'
    )
    for path in article_paths:
        print(f'{BOLD}{escape_spaces_in_path(path)}{RESET}')

    input()

    return tuple(open(path, 'r').read() for path in article_paths)


def create_empty_file_if_not_exists(file_path: str) -> None:
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write('')


def escape_spaces_in_path(path: str) -> str:
    return path.replace(' ', '\\ ')


if __name__ == '__main__':
    main()
