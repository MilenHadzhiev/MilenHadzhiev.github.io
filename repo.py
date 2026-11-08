import net

from collections.abc import Iterator

from functools import cached_property
from typing import Final

from constants import HEADERS
from release import Release

class Repository:
    def __init__(self, repo_data: dict) -> None:
        self.__repo: Final = repo_data

    @cached_property
    def name(self) -> str:
        return self.__repo['name']

    @cached_property
    def url(self) -> str:
        return self.__repo['url']

    @cached_property
    def homepage(self) -> str:
        return self.__repo['homepage']

    @cached_property
    def owner(self) -> str:
        return self.__repo['owner']['login']

    @cached_property
    def html_url(self) -> str:
        return self.__repo.get('html_url') or ''

    @cached_property
    def description(self) -> str:
        return self.__repo.get('description') or ''

    @cached_property
    def stars(self) -> int:
        return self.__repo.get('stargazers_count') or 0

    @cached_property
    def forks_count(self) -> int:
        return self.__repo.get('forks_count') or 0

    @cached_property
    def topics(self) -> list[str]:
        return self.__repo.get('topics') or []

    @cached_property
    def pushed_at(self) -> str:
        return self.__repo.get('pushed_at') or ''

    @cached_property
    def archived(self) -> bool:
        return bool(self.__repo.get('archived'))

    @cached_property
    def fork(self) -> bool:
        return bool(self.__repo.get('fork'))

    @cached_property
    def language(self) -> str:
        return self.__repo['language']

    @cached_property
    def languages(self) -> dict[str, float]:
        url = f'{self.__repo['languages_url']}'

        r = net.get(url, headers=HEADERS)
        r.raise_for_status()

        languages = r.json()
        total = sum(languages.values())
        if not total:
            return {}
        return {
            lang: round(lines / total * 100, 2)
            for lang, lines in languages.items()
        }

    @property
    def releases(self) -> Iterator[Release]:
        url = f'{self.url}/releases?per_page=100'

        releases = []
        while url:
            r = net.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            yield from (Release(item) for item in r.json())
            url = r.links.get("next", {}).get("url")

