import logging
import os
import sys

from tts import Narrator
from bs4 import BeautifulSoup
from ebooklib import epub
from pathlib import Path

logFormatter = logging.Formatter("%(asctime)s [%(funcName)20s] [%(levelname)-8.8s]  %(message)s")
logger = logging.getLogger()
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.DEBUG)


def sanitize_text(text: str) -> str:
    """Remove / replace unwanted characters from text
    Args:
        text (str): The text to be celaned
    Returns:
        (str): The cleaned text
    """
    text = text.replace('?', '')
    text = text.replace('#', '﹟')
    while '"' in text:
        text = text.replace('"', '“', 1)
        text = text.replace('"', '”', 1)
    text = text.replace("'", 'ʼ')
    text = text.replace(':', '꞉')
    text = text.replace('*', '⋆')
    text = text.replace('|', '┃')
    text = text.replace('/', '⁄')
    text = text.replace('\\', '﹨')
    text = text.replace('<', '＜')
    text = text.replace('>', '＞')
    if text[-1:] == ".":
        text = text[:-1]
    return text.strip()


def extract_text(src):
    soup = BeautifulSoup(src, 'html.parser')
    text = soup.find_all(text=True)

    output = []
    blacklist = [
        '[document]',
        'noscript',
        'header',
        'html',
        'meta',
        'head',
        'input',
        'script',
    ]

    for t in text:
        if t.parent.name not in blacklist and t.strip():
            output.append(t)

    return output


def main():
    if os.path.exists('service_account.json'):
        # TODO: No idea (yet) how to load this file, so let's just set an ENV variable :)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"

    if len(sys.argv) != 2:
        logger.critical('Required argument missing: ebook filename')
        sys.exit(1)

    ebook = sys.argv[1]
    if not os.path.exists(ebook):
        logger.critical(f'File not found: {ebook}')
        sys.exit(1)

    book = epub.read_epub(ebook)
    title = book.get_metadata('DC', 'title')
    creator = book.get_metadata('DC', 'creator')
    toc = book.toc

    logger.info(f'Title: {title}')
    logger.info(f'Author: {creator}')
    chapter_counter = 1

    for chapter in toc:
        logger.debug(f'Processing chapter: {chapter.title}')
        chapter_content = book.get_item_with_href(chapter.href).get_body_content().decode('utf-8')
        chapter_content_text = extract_text(chapter_content)
        if len(chapter_content_text) > 0:
            logger.debug('Processing lines...')
            opus_path = Path(f'{Path(ebook).stem}_{str(chapter_counter).zfill(2)}_{sanitize_text(chapter.title)}').with_suffix(".opus")
            narrator = Narrator()
            narrator.text_to_opus(chapter_content_text, opus_path)
            chapter_counter += 1
        else:
            logger.debug(f'Skipping chapter: no text')


if __name__ == "__main__":
    main()
