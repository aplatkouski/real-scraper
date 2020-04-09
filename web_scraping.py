#!/usr/bin/env python

from typing import Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

URL = 'https://realpython.com/'
_CACHED_CONTENT = dict()


def get_page(url: str) -> BeautifulSoup:
    """
    Download data on the first request

    Save the downloaded page to the cache on the first request
    and return data from the cash on subsequent calls
    """
    if url not in _CACHED_CONTENT:
        result = requests.get(url)
        if result.status_code == 200:
            _CACHED_CONTENT[url] = BeautifulSoup(result.content,
                                                 features='html.parser')
    return _CACHED_CONTENT[url]


class Article:
    """
    Class with unique instances
    """

    _instances = dict()

    card_param = {'name': 'div', 'attrs': {'class': 'card border-0'}}
    title_param = {'name': 'h2', 'attrs': {'class': 'card-title'}}
    date_param = {'name': 'span', 'attrs': {'class': ['mr-2']}}

    def __new__(cls, heading: str, url: str, tags: set, date: str = None):
        hash_ = hash(url)
        if hash_ not in Article._instances:
            Article._instances[hash_] = super(Article, cls).__new__(cls)
        return Article._instances[hash_]

    def __init__(self, heading: str, url: str, tags: set, date: str = None):
        self.heading: str = heading
        self.url: str = url
        self.date: str = date
        self.tags: set = tags

    def __str__(self):
        return f"[{self.heading}]({self.url})\n"

    def __repr__(self):
        return (f"Article(heading='{self.heading}'"
                f", url='{self.url}'"
                f", date='{self.date}'"
                f", tags='{self.tags}')")

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.url == other.url)

    def __ne__(self, other):
        return not (self.__class__ == other.__class__ and
                    self.url == other.url)

    def str_markdown(self, as_task: bool = False) -> str:
        prefix: str = ""
        if as_task:
            prefix = f" - [ ] "
        if urlparse(self.url).path.startswith('/courses/'):
            prefix = f"{prefix}Course: "
        title = f"{prefix}[{self.heading}]({self.url})\n"
        date_string = (f"*{self.date}* | " if self.date else "")
        tags_string = (' '.join([f"`{tag.topic}`" for tag in self.tags])
                       if self.tags else "")
        return ''.join([title, date_string, tags_string])

    def write_to_file(self, file: str = 'README.md', force: bool = True) -> None:
        """
        Record info about article in file (as markdown task '[ ]')

        If file has article-link no data will be recorded.
        Else the article will be recorded only once
        under an appropriate tag heading in the end of the file.
        Hence, last tag headings have higher priority than opening tag.

        If tag heading isn't found, add record in the end of the file
        """
        with open(file, 'r') as fr:
            text: str = fr.read()
        if text.find(self.url) == -1:
            text_list: list = text.split('\n\n')
            for n in reversed(range(len(text_list))):
                if any([text_list[n].find(tag.main_url) != - 1
                        for tag in self.tags]):
                    text_list = (text_list[:n + 1] +
                                 [f"{self.str_markdown(as_task=True)}", ] +
                                 text_list[n + 1:])
                    with open(file, 'w') as fw:
                        fw.write('\n\n'.join(text_list))
                    return
            # if tags from article don't found in file and `force=True`
            if force:
                text = '\n\n'.join((text,
                                    '# New article(-s)',
                                    f"{self.str_markdown(as_task=True)}"))
                with open(file, 'w') as fw:
                    fw.write(text)


def get_articles(url: str) -> Set[Article]:
    """
    Return set of all articles on the page
    """
    articles: set = set()
    website_url = '://'.join(urlparse(url)[:2])
    for card in get_page(url).find_all(**Article.card_param):
        title: str = card.find(**Article.title_param).string
        href: str = urljoin(website_url, card.a['href'])
        try:
            date: str = card.find(**Article.date_param).string
        except AttributeError:
            date: str = ""
        tags: set = set()
        for badge in card.find_all(**Tag.badge_param):
            tag = Tag(topic=badge.string,
                      url=urljoin(website_url, badge['href']))
            tags.add(tag)
        articles.add(Article(heading=title, url=href, tags=tags, date=date))
    return articles


class Tag:
    """
    Class with unique instances
    """

    _instances = dict()

    sidebar_param = {'name': 'div', 'attrs': {'class': 'sidebar-module'}}
    badge_param = {'name': 'a', 'attrs': {'class': 'badge'}, 'href': True}
    page_link_param = {'name': 'a', 'attrs': {"class": "page-link"},
                       'href': True}

    def __new__(cls, topic: str, url: str):
        hash_ = hash(url)
        if hash_ not in Tag._instances:
            Tag._instances[hash_] = super(Tag, cls).__new__(cls)
        return Tag._instances[hash_]

    def __init__(self, topic: str, url: str):
        self.topic: str = topic
        self.heading: str = ""
        self.main_url: str = url
        self.urls: set = {url, }
        self._extract_heading()
        self._extract_all_urls()

    def __str__(self):
        return (f"[{self.heading if self.heading else self.topic}]"
                f"({self.main_url})")

    def __hash__(self):
        return hash(self.main_url)

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.main_url == other.main_url)

    def __ne__(self, other):
        return not (self.__class__ == other.__class__ and
                    self.main_url == other.main_url)

    def _extract_heading(self):
        self.heading = get_page(self.main_url).h1.string

    def _extract_all_urls(self) -> None:
        """
        Save the url of all pages with articles
        """
        soup: BeautifulSoup = get_page(self.main_url)
        website_url = '://'.join(urlparse(self.main_url)[:2])
        all_urls = [urljoin(website_url, page_link['href'])
                    for page_link in soup.find_all(**Tag.page_link_param)]
        self.urls.update(all_urls)

    def get_all_articles(self) -> Set[Article]:
        all_articles: set = set()
        for url in self.urls:
            all_articles.update(get_articles(url))
        return all_articles

    def write_to_file(self, file: str = 'README.md') -> None:
        """
        Record info about tag in file (as markdown heading '^# ')

        If file has tag-link no data will be recorded.
        """
        with open(file, 'r') as fr:
            text: str = fr.read()
        if text.find(self.main_url) == -1:
            text = '\n\n'.join((text, f"# {self}"))
            with open(file, 'w') as fw:
                fw.write(text)


def get_all_tags(website_url: str) -> Set[Tag]:
    tags: set = set()
    for sidebar in get_page(website_url).find_all(**Tag.sidebar_param):
        for badge in sidebar.find_all(**Tag.badge_param):
            tag = Tag(topic=badge.string,
                      url=urljoin(website_url, badge['href']))
            tags.add(tag)
    return tags


def main(url=URL) -> None:
    all_articles: set = set()
    for tag in get_all_tags(url):
        all_articles.update(tag.get_all_articles())
        tag.write_to_file()
    for article in all_articles:
        article.write_to_file()


if __name__ == '__main__':
    main()
