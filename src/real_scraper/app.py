#!/usr/bin/env python

from typing import ClassVar, Dict, List, Set, Union
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup  # type: ignore
from requests import Response  # noqa

FilterByOneClass = Dict[str, str]
FilterByMultipleClass = Dict[str, List[str]]
ClassParam = Dict[str, Union[FilterByOneClass, FilterByMultipleClass, bool, str]]

URL: str = 'https://realpython.com/'
_cached_content: Dict[str, 'BeautifulSoup'] = dict()


def get_beautifulsoup(url: str) -> BeautifulSoup:
    """
    Download data on the first request

    Save the downloaded page to the cache on the first request
    and return data from the cash on subsequent calls
    """
    if url not in _cached_content:
        response: Response = requests.request('GET', url, timeout=(3.0, 5.0))
        if response:
            _cached_content[url] = BeautifulSoup(response.content, features='lxml')
        else:
            response.raise_for_status()
    return _cached_content[url]


class Article:
    """
    Class with unique instances
    """

    _instances: ClassVar[Dict[int, 'Article']] = dict()

    card_param: ClassVar[ClassParam] = {
        'name': 'div',
        'attrs': {'class': 'card border-0'},
    }
    title_param: ClassVar[ClassParam] = {'name': 'h2', 'attrs': {'class': 'card-title'}}
    date_param: ClassVar[ClassParam] = {'name': 'span', 'attrs': {'class': ['mr-2']}}

    def __new__(cls, heading: str, url: str, tags: set, date: str = '') -> 'Article':
        hash_: int = hash(url)
        if hash_ not in Article._instances:
            Article._instances[hash_] = super(Article, cls).__new__(cls)
        return Article._instances[hash_]

    def __init__(self, heading: str, url: str, tags: set, date: str = '') -> None:
        self.heading: str = heading
        self.url: str = url
        self.date: str = date
        self.tags: set = tags

    def __str__(self) -> str:
        return f"[{self.heading}]({self.url})\n"

    def __repr__(self) -> str:
        return (
            f"Article(heading='{self.heading}'"
            f", url='{self.url}'"
            f", date='{self.date}'"
            f", tags='{self.tags}')"
        )

    def __hash__(self) -> int:
        return hash(self.url)

    def __eq__(self, other) -> bool:
        return self.__class__ == other.__class__ and self.url == other.url

    def __ne__(self, other) -> bool:
        return not (self.__class__ == other.__class__ and self.url == other.url)

    def str_markdown(self, as_task: bool = False) -> str:
        prefix: str = ""
        if as_task:
            prefix = f" - [ ] "
        if urlparse(self.url).path.startswith('/courses/'):
            prefix = f"{prefix}Course: "
        title: str = f"{prefix}[{self.heading}]({self.url})\n"
        date_string: str = (f"*{self.date}* | " if self.date else "")
        tags_string: str = (' '.join([f"`{tag.topic}`" for tag in self.tags]))
        return ''.join([title, date_string, tags_string])

    def _is_any_url_of_tags_in_string(self, line: str) -> bool:
        return any([line.find(tag.main_url) != -1 for tag in self.tags])

    def write_to_file(self, file: str = 'README.md', force: bool = True) -> None:
        """
        Record info about article in file (as Markdown)

        If file has article-link no data will be recorded.
        Else the article will be recorded only once
        under an appropriate tag heading in the end of the file.
        Hence, last tag headings have higher priority than opening tag.

        If tag heading isn't found, add record in the end of the file
        """
        with open(file, 'r') as fr:
            text: str = fr.read()
        if text.find(self.url) == -1:
            list_of_strings: list = text.split('\n\n')
            for n in reversed(range(len(list_of_strings))):
                if self._is_any_url_of_tags_in_string(list_of_strings[n]):
                    list_of_strings = (
                            list_of_strings[:n + 1]
                            + [f"{self.str_markdown(as_task=True)}", ]
                            + list_of_strings[n + 1:]
                    )
                    with open(file, 'w') as fw:
                        fw.write('\n\n'.join(list_of_strings))
                    return
            # if tags from article don't found in file and `force=True`
            if force:
                with open(file, 'a') as fa:
                    fa.write("\n\n# New article\n\n{self.str_markdown(as_task=True)}")


def get_articles(url: str) -> Set[Article]:
    """
    Return set of all articles on the page
    """
    articles: Set[Article] = set()
    website_url: str = '://'.join(urlparse(url)[:2])
    for card in get_beautifulsoup(url).find_all(**Article.card_param):
        title: str = str(card.find(**Article.title_param).string)
        href: str = urljoin(website_url, card.a['href'])
        try:
            date: str = str(card.find(**Article.date_param).string)
        except AttributeError:
            date = ""
        tags: Set[Tag] = set(
            Tag(topic=str(badge.string), url=urljoin(website_url, badge['href']))
            for badge in card(**Tag.badge_param)
        )
        articles.add(Article(heading=title, url=href, tags=tags, date=date))
    return articles


class Tag:
    """
    Class with unique instances
    """

    _instances: ClassVar[Dict[int, 'Tag']] = dict()

    sidebar_param: ClassVar[ClassParam] = {
        'name': 'div',
        'attrs': {'class': 'sidebar-module'},
    }
    badge_param: ClassVar[ClassParam] = {
        'name': 'a',
        'attrs': {'class': 'badge'},
        'href': True,
    }
    page_link_param: ClassVar[ClassParam] = {
        'name': 'a',
        'attrs': {"class": "page-link"},
        'href': True,
    }

    def __new__(cls, topic: str, url: str) -> 'Tag':
        hash_: int = hash(url)
        if hash_ not in Tag._instances:
            Tag._instances[hash_] = super(Tag, cls).__new__(cls)
        return Tag._instances[hash_]

    def __init__(self, topic: str, url: str) -> None:
        self.topic: str = topic
        self.heading: str = ""
        self.main_url: str = url
        self.urls: set = {
            url,
        }
        self._extract_heading()
        self._extract_all_urls()

    def __str__(self) -> str:
        return f"[{self.heading if self.heading else self.topic}]({self.main_url})"

    def __hash__(self) -> int:
        return hash(self.main_url)

    def __eq__(self, other) -> bool:
        return self.__class__ == other.__class__ and self.main_url == other.main_url

    def __ne__(self, other) -> bool:
        return not (
                self.__class__ == other.__class__ and self.main_url == other.main_url
        )

    def _extract_heading(self) -> None:
        self.heading = str(get_beautifulsoup(self.main_url).h1.string)

    def _extract_all_urls(self) -> None:
        """
        Save the url of all pages with articles
        """
        soup: BeautifulSoup = get_beautifulsoup(self.main_url)
        website_url: str = '://'.join(urlparse(self.main_url)[:2])
        all_urls: List[str] = [
            urljoin(website_url, page_link['href'])
            for page_link in soup(**Tag.page_link_param)
        ]
        self.urls.update(all_urls)

    def get_all_articles(self) -> Set[Article]:
        all_articles: Set[Article] = set()
        for url in self.urls:
            all_articles.update(get_articles(url))
        return all_articles

    def write_to_file(self, file: str = 'README.md') -> None:
        """
        Write tag in file (as markdown heading '^# ')

        If file has tag-link no data will be recorded.
        """
        with open(file, 'r+') as f:
            text: str = f.read()
            if text.find(self.main_url) == -1:
                text = '\n\n'.join((text, f"# {self}"))
                f.write(text)


def get_all_tags(website_url: str) -> Set[Tag]:
    tags: Set[Tag] = set()
    for sidebar in get_beautifulsoup(website_url).find_all(**Tag.sidebar_param):
        tags.union(
            set(
                Tag(topic=str(badge.string), url=urljoin(website_url, badge['href']))
                for badge in sidebar(**Tag.badge_param)
            )
        )

    return tags


def main(url=URL) -> None:
    all_articles: Set[Article] = set()
    for tag in get_all_tags(url):
        all_articles.update(tag.get_all_articles())
        tag.write_to_file()
    for article in all_articles:
        article.write_to_file()


if __name__ == '__main__':
    main()
