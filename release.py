from functools import cached_property


class Release:
    def __init__(self, data: dict) -> None:
        self.__release = data

    @cached_property
    def tag(self) -> Version:
        return Version(self.__release['tag_name'])

    @cached_property
    def name(self) -> str | Version:
        return self.__release.get('name', self.tag)

    @cached_property
    def notes(self) -> str:
        """release notes"""
        return self.__release['body']

    @cached_property
    def page(self) -> str:
        """release page on github"""
        return self.__release['html_url']
    # TODO: Add more info -> auto-generated archives, assets, commit from which the tag was created...

