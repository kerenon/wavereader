import logging
import os
import sys

from tts import Narrator
from bs4 import BeautifulSoup
from ebooklib import epub
from pathlib import Path

logFormatter = logging.Formatter("%(asctime)s [%(funcName)20s] [%(levelname)-8.8s]  %(message)s")
logger = logging.getLogger('wavereader')
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)


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
    for script in soup(["script", "style"]):
        script.extract()
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
        'title'
    ]

    for t in text:
        if t.parent.name not in blacklist and t.strip():
            output.append(t)

    return output


def is_chapter_marker(element, toc):
    for t in toc:
        if Path(element).name == Path(t.href).name.split('#')[0]:
            return True


def get_chapter_title(element, toc):
    for t in toc:
        if Path(element).name == Path(t.href).name.split('#')[0]:
            return t.title


def main():
    if Path('service_account.json').exists():
        # TODO: No idea (yet) how to load this file, so let's just set an ENV variable :)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"

    if len(sys.argv) != 2:
        logger.critical('Required argument missing: ebook filename')
        sys.exit(1)

    ebook = sys.argv[1]
    if not Path(ebook).exists():
        logger.critical(f'File not found: {ebook}')
        sys.exit(1)

    book = epub.read_epub(ebook)
    title = book.title
    author = ''

    for creator in book.get_metadata('DC', 'creator'):
        creator_name = creator[0]
        creator_tags = creator[1]
        if 'id' in creator_tags.keys():
            if creator_tags['id'] == 'id-1':
                author = creator_name
                break

    if not author:
        logger.info(f'Unable to determine book author. Please enter author name, or leave empty to use "Unknown":')
        author = input()
        if author == '':
            author = 'Unknown'

    logger.info(f'Title: {title}')
    logger.info(f'Author: {author}')

    chapter_title = ''
    last_chapter = ''
    book_content = [book.get_item_with_id(e[0]).get_name() for e in book.spine]

    joblist = {}
    book_length = 0

    for element in book_content:
        if is_chapter_marker(element, book.toc):
            chapter_title = get_chapter_title(element, book.toc)
            if chapter_title != last_chapter:
                last_chapter = chapter_title
        logger.debug(f'Processing chapter: >{chapter_title}<')
        element_content = book.get_item_with_href(element).content.decode('utf-8')
        element_content_text = extract_text(element_content)

        if len(element_content_text) <= 10:
            continue
        if chapter_title == '':
            continue

        if chapter_title in joblist:
            joblist[chapter_title].extend(element_content_text)
        else:
            joblist[chapter_title] = element_content_text

    for job in joblist:
        for line in joblist[job]:
            book_length += len(line.strip())
    logger.info(f'This books length is ~{book_length} characters. To continue, press [ENTER], and [CTRL-C] to quit!')
    input()

    narrator = Narrator()
    for counter, job in enumerate(joblist.keys(), start=1):
        logger.info(f'Processing chapter [{counter}/{len(joblist)}]: "{job}"')
        flac_path = Path(f'{Path(ebook).stem}_{str(counter).zfill(3)}_{sanitize_text(job)}').with_suffix(".flac")
        if Path(flac_path).exists():
            logger.info(f'File "{flac_path}" already exists. Skipping.')
            continue
        narrator.author = author
        narrator.album_title = title
        narrator.title = job
        narrator.track_number = counter
        if Path(ebook).with_suffix('.jpg').exists():
            narrator.coverfile = Path(ebook).with_suffix('.jpg')
        elif Path(ebook).with_suffix('.png').exists():
            narrator.coverfile = Path(ebook).with_suffix('.png')
        narrator.text_to_flac(joblist[job], flac_path)
    logger.info(f'Characters used for conversion: {narrator.used_characters}')


if __name__ == "__main__":
    main()
