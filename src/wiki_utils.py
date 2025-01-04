def read_article(article_name: str) -> str:
    with open(f'contents/{article_name}.wikitext', 'r') as f:
        return f.read()

def replace_article_lines(article_name: str, new_text: list[str] | str, start: int, end: int):
    if isinstance(new_text, str):
        new_text = new_text.splitlines()

    new_full_lines = read_article(article_name).splitlines() + ['']
    new_full_lines[start:end] = new_text
    new_text = '\n'.join(new_full_lines)
    with open(f'contents/{article_name}.wikitext', 'w') as f:
        f.write(new_text)
