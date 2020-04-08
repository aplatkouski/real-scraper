#!./.venv/bin/python
"""
scraping online articles from realpython.com

- [x] get all tags (badges) from main page of the site
- [x] Open main page of each tag and get links of pages
- [x] get articles from all pages of tag
- [ ] refactoring
- [ ] save articles in text file (markdown)
- [ ] create one list with titles of all articles (+tags, + public date)
"""

from typing import Set, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

URL = 'https://realpython.com/'
_CACHED_CONTENT = dict()


def get_page(url: str) -> bytes:
    if url not in _CACHED_CONTENT:
        result = requests.get(url)
        if result.status_code == 200:
            _CACHED_CONTENT[url] = result.content
    return _CACHED_CONTENT[url]


class Article:

    def __init__(self, heading: str, url: str, date: str, tags: list):
        self.heading: str = heading
        self.url: str = url
        self.date: str = date
        self.tags: dict = dict()
        for tag in tags:
            self.tags[tag.string] = tag.attrs['href']

    def __str__(self):
        result = (f"\n# {self.heading}\n"
                  f"{self.date} || {self.url}\n")
        for tag in self.tags.keys():
            result = f"{result} @{tag}"
        return result


class Tag:

    def __init__(self, topic: str, url: str):
        self.topic: str = topic
        self.main_url = url
        self.urls: set = set()

    def __str__(self):
        result = f"\n@{self.topic}\n\t{self.main_url}\n"
        for url in self.urls:
            result = f"{result}\t{url}\n"
        return result


def get_articles(url: str) -> List[Article]:
    src: bytes = get_page(url)
    soup: BeautifulSoup = BeautifulSoup(src, features='html.parser')
    articles = soup.find_all(name='div', attrs={'class': 'card border-0'})
    articles_list = list()
    for article in articles:
        title = article.find(name='h2', attrs={'class': 'card-title'}).string
        href = urljoin(url, article.a['href'])
        try:
            date = article.find(name='span', attrs={'class': ['mr-2']}).string
        except AttributeError:
            date = ""
        badges = article.find_all(name='a',
                                  attrs={'class': 'badge'},
                                  href=True)
        articles_list.append(Article(heading=title, url=href,
                                     date=date, tags=badges))
    return articles_list


def get_all_tutorial_tags(url: str) -> Set[Tag]:
    tags = set()
    src: bytes = get_page(url)
    soup: BeautifulSoup = BeautifulSoup(src, features='html.parser')
    tutorial_topics_sidebars = soup.find_all(name="div",
                                             attrs={"class": "sidebar-module"})
    for sidebar in tutorial_topics_sidebars:
        badges = sidebar.find_all(name="a",
                                  attrs={"class": "badge"},
                                  href=True)
        for badge in badges:
            tags.add(Tag(topic=badge.string,
                         url=urljoin(url, badge['href'])))
    return tags


def get_all_page_links_of_tags(url: str, tags: Set[Tag]):
    for tag in tags:
        src: bytes = get_page(tag.main_url)
        soup: BeautifulSoup = BeautifulSoup(src, features='html.parser')
        page_link_elements = soup.find_all(name="a",
                                           attrs={"class": "page-link"},
                                           href=True)
        for page_link_element in page_link_elements:
            tag.urls.add(urljoin(url, page_link_element['href']))


def get_all_articles_list(tags: Set[Tag]) -> List[Article]:
    all_articles: list = list()
    for tag in tags:
        all_articles.extend(get_articles(tag.main_url))
        for url in tag.urls:
            all_articles.extend(get_articles(tag.main_url))
    return all_articles


def main(url=URL) -> None:
    tags = get_all_tutorial_tags(url)
    get_all_page_links_of_tags(url, tags)
    all_articles = get_all_articles_list(tags)
    for article in all_articles:
        print(article)


if __name__ == '__main__':
    main()
