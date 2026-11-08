"""HTTP for both environments.

Natively this is just `requests`. Under WASI there are no sockets, so `get`
answers from responses the host (JS) already fetched and handed over in
RESPONSES_PATH. A URL that isn't there yet is recorded in MISSING and
NeedFetch is raised; the host fetches MISSING and runs us again.
"""
import json
import sys

RESPONSES_PATH = '/data/responses.json'


class NeedFetch(Exception):
    def __init__(self, url: str) -> None:
        super().__init__(url)
        self.url = url


MISSING: list[str] = []

if sys.platform != 'wasi':
    import requests

    HTTPError = requests.HTTPError

    def get(url: str, headers: dict | None = None, timeout: float | None = None):
        return requests.get(url, headers=headers, timeout=timeout)

else:
    class HTTPError(Exception):
        def __init__(self, message: str, response: 'Response') -> None:
            super().__init__(message)
            self.response = response

    class Response:
        def __init__(self, entry: dict) -> None:
            self.status_code: int = entry['status']
            self.text: str = entry['body']
            self.links = _parse_links(entry.get('link'))

        def json(self):
            return json.loads(self.text)

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise HTTPError(f'HTTP {self.status_code}', self)

    def _parse_links(header: str | None) -> dict[str, dict[str, str]]:
        """'<url>; rel="next", ...' -> {'next': {'url': url, 'rel': 'next'}}, like requests."""
        links = {}
        for part in (header or '').split(','):
            url_part, _, params = part.partition(';')
            url = url_part.strip().strip('<>')
            for param in params.split(';'):
                key, _, value = param.strip().partition('=')
                if key == 'rel' and url:
                    rel = value.strip('"')
                    links[rel] = {'url': url, 'rel': rel}
        return links

    _responses: dict[str, dict] | None = None

    def _load() -> dict[str, dict]:
        global _responses
        if _responses is None:
            try:
                with open(RESPONSES_PATH) as f:
                    _responses = json.load(f)
            except FileNotFoundError:
                _responses = {}
        return _responses

    def get(url: str, headers: dict | None = None, timeout: float | None = None):
        # headers/timeout are ignored: the browser decides how to send the request.
        entry = _load().get(url)
        if entry is None:
            if url not in MISSING:
                MISSING.append(url)
            raise NeedFetch(url)
        return Response(entry)
