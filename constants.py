import os

TOKEN = os.environ.get('GITHUB_TOKEN')

ACCOUNT = 'MilenHadzhiev'

FEATURED: list[str] = []
FEATURED_COUNT = 3

CONTACT_EMAIL = 'milenhadzhiev@proton.me'

HEADERS = {
    'Accept': 'application/vnd.github+json',
    'User-Agent': 'MilenHadzhiev',
}
if TOKEN:
    HEADERS['Authorization'] = f'Bearer {TOKEN}'
