import net

from constants import HEADERS
from repo import Repository


def fetch_repos(user: str) -> list[Repository]:
    response = net.get(f'https://api.github.com/users/{user}/repos', headers=HEADERS)
    response.raise_for_status()
    return [Repository(repo_data) for repo_data in response.json()]


def fetch_profile(user: str) -> dict:
    response = net.get(f'https://api.github.com/users/{user}', headers=HEADERS)
    response.raise_for_status()
    return response.json()


def fetch_social_accounts(user: str) -> list[dict]:
    response = net.get(f'https://api.github.com/users/{user}/social_accounts', headers=HEADERS)
    response.raise_for_status()
    return response.json()
