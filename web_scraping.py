#!./.venv/bin/python
"""
scraping online articles from realpython.com

- [x] get all tags (badges) from main page of the site
- [ ] Open main page of each tag and get count of pages
- [ ] get articles from all pages of tag
- [ ] save articles in  text file (markdown)
- [ ] create one list with titles of all articles (+tags, + public date)
"""

import urllib

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


class Topic:

    def __init__(self, heading: str, url: str, date: str, tags: list):
        self.heading: str = heading
        self.url: str = url
        self.date: str = date
        self.tags: dict = dict()
        for tag in tags:
            self.tags[tag.text] = tag.attrs['href']

    def __str__(self):
        result = (f"\n# {self.heading}\n"
                  f"{self.date} || {self.url}\n")
        for tag in self.tags.keys():
            result = f"{result} @{tag}"
        return result


def get_main_page_articles(url):
    src: bytes = get_page(url)
    soup: BeautifulSoup = BeautifulSoup(src, features='html.parser')
    topics = soup.find_all(name='div', attrs={'class': 'card border-0'})
    topics_list = list()
    for topic in topics:
        heading = topic.find(name='h2', attrs={'class': 'card-title'}).text
        topic_url = urllib.parse.urljoin(url, topic.a['href'])
        date = topic.find(name='span', attrs={'class': ['mr-2']}).text
        tags = topic.find_all(name='a', attrs={'class': 'badge'})
        topics_list.append(Topic(heading, topic_url, date, tags))
    for topic in topics_list:
        print(topic)


def get_all_tutorial_badges(url: str) -> dict:
    src: bytes = get_page(url)
    soup: BeautifulSoup = BeautifulSoup(src, features='html.parser')
    tutorial_topics_sidebars = soup.find_all("div", {"class": "sidebar-module"})
    for sidebar in tutorial_topics_sidebars:
        badge_tags = sidebar.find_all("a", {"class": "badge"}, href=True)
        badges = dict()
        for badge in badge_tags:
            badges[badge.text] = urllib.parse.urljoin(url, badge.attrs['href'])
    return badges


def main(url=URL) -> None:
    tags = get_all_tutorial_badges(url)
    print(tags)


if __name__ == '__main__':
    main()
