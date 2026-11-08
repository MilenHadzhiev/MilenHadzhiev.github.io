import os

TOKEN = os.environ.get('GITHUB_TOKEN')

ACCOUNT = 'MilenHadzhiev'

# Pinned repos, in order. Empty = most starred.
FEATURED: list[str] = []
FEATURED_COUNT = 3

# Falls back to the public email on the GitHub profile.
CONTACT_EMAIL = ''

HEADERS = {
    'Accept': 'application/vnd.github+json',
    'User-Agent': 'MilenHadzhiev',
}
if TOKEN:
    HEADERS['Authorization'] = f'Bearer {TOKEN}'
