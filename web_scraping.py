#!./.venv/bin/python
"""
scraping online articles from realpython.com

- [x] get all tags (badges) from main page of the site
- [x] Open main page of each tag and get links of pages
- [x] get articles from all pages of tag
- [x] refactoring
- [ ] save articles in text file (markdown)
- [ ] create one list with titles of all articles (+tags, + public date)
"""

from typing import Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

URL = 'https://realpython.com/'
_CACHED_CONTENT = dict()


def get_page(url: str) -> BeautifulSoup:
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

    card_param = {'name': 'div', 'attrs': {'class': 'card border-0'}}
    title_param = {'name': 'h2', 'attrs': {'class': 'card-title'}}
    date_param = {'name': 'span', 'attrs': {'class': ['mr-2']}}
    _instances = dict()

    def __new__(cls, heading: str, url: str,
                date: str = None, tags: list = None):
        hash_ = hash(url)
        if hash_ not in Article._instances:
            Article._instances[hash_] = super(Article, cls).__new__(cls)
        return Article._instances[hash_]

    def __init__(self, heading: str, url: str,
                 date: str = None, tags: list = None):
        self.heading: str = heading
        self.url: str = url
        self.date: str = date
        self.tags: dict = dict()
        self.tags = {tag.string: tag.attrs['href'] for tag in tags}

    def __str__(self):
        full_title = (f"# {self.heading}\n*{self.date}* || {self.url}"
                      if self.date
                      else f"# {self.heading}\n{self.url}")
        tags_string = (' '.join([f"@{tag}" for tag in self.tags])
                       if self.tags
                       else "")
        return '\n\n'.join([full_title, tags_string, ""])

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


def get_articles(url: str) -> Set[Article]:
    articles = set()
    for card in get_page(url).find_all(**Article.card_param):
        title: str = card.find(**Article.title_param).string
        href: str = urljoin('://'.join(urlparse(url)[:2]), card.a['href'])
        try:
            date: str = card.find(**Article.date_param).string
        except AttributeError:
            date: str = ""
        badges = card.find_all(**Tag.badges_param)
        articles.add(Article(heading=title, url=href,
                             date=date, tags=badges))
    return articles


class Tag:
    """
    Class with unique instances
    """

    _instances = dict()
    sidebar_param = {'name': 'div', 'attrs': {'class': 'sidebar-module'}}
    badges_param = {'name': 'a', 'attrs': {'class': 'badge'}, 'href': True}
    page_link_param = {'name': 'a', 'attrs': {"class": "page-link"},
                       'href': True}

    def __new__(cls, topic: str, url: str):
        hash_ = hash(url)
        if hash_ not in Tag._instances:
            Tag._instances[hash_] = super(Tag, cls).__new__(cls)
        return Tag._instances[hash_]

    def __init__(self, topic: str, url: str):
        self.topic: str = topic
        self.main_url = url
        self.urls: set = {url, }

    def __str__(self):
        urls_string = '\n\t'.join([url for url in self.urls])
        return f"@{self.topic}\n{urls_string}"

    def __hash__(self):
        return hash(self.main_url)

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.main_url == other.main_url)

    def __ne__(self, other):
        return not (self.__class__ == other.__class__ and
                    self.main_url == other.main_url)

    def find_and_save_all_urls(self, website_url: str) -> None:
        soap: BeautifulSoup = get_page(self.main_url)
        all_urls = [urljoin(website_url, page_link['href'])
                    for page_link in soap.find_all(**Tag.page_link_param)]
        self.urls.update(all_urls)

    def get_all_articles(self) -> Set[Article]:
        all_articles: set = set()
        for url in self.urls:
            all_articles.update(get_articles(url))
        return all_articles


def get_all_tags(website_url: str) -> Set[Tag]:
    tags: set = set()
    for sidebar in get_page(website_url).find_all(**Tag.sidebar_param):
        for badge in sidebar.find_all(**Tag.badges_param):
            tag = Tag(topic=badge.string,
                      url=urljoin(website_url, badge['href']))
            tag.find_and_save_all_urls(website_url)
            tags.add(tag)
    return tags


def main(url=URL) -> None:
    all_articles: set = set()
    for tag in get_all_tags(url):
        all_articles.update(tag.get_all_articles())
    for article in all_articles:
        print(article)


if __name__ == '__main__':
    main()
