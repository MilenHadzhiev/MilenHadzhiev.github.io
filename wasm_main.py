"""WASI entry point. Prints one JSON line:

  {"need": [urls...]}   fetch these, add them to /data/responses.json, run again
  {"html": "..."}       finished markup for #output
"""
import json
import os
import re
from html import escape

import net
from constants import ACCOUNT, CONTACT_EMAIL, FEATURED, FEATURED_COUNT
from github import fetch_profile, fetch_repos, fetch_social_accounts
from repo import Repository

TOP_LANGUAGES = 3
USERNAME_PATTERN = r'[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}'
USERNAME = re.compile(USERNAME_PATTERN)


def requested_account() -> str:
    return os.environ.get('GITHUB_USER', '').strip() or ACCOUNT


def render_search(account: str) -> str:
    return (
        '<form class="search" method="get" role="search">'
        f'<input id="user" name="user" type="search" value="{escape(account)}" '
        'placeholder="GitHub username" autocomplete="off" spellcheck="false" '
        f'maxlength="39" pattern="{escape(USERNAME_PATTERN)}" required>'
        '<label class="search-toggle" for="user" title="Search GitHub user">'
        '<span class="visually-hidden">GitHub username</span>'
        '<svg viewBox="0 0 24 24" aria-hidden="true">'
        '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'
        '</label>'
        '</form>'
    )


def render_toolbar(account: str) -> str:
    note = ''
    if account.lower() != ACCOUNT.lower():
        note = (
            '<p class="viewing">Showing '
            f'<strong>{escape(account)}</strong>'
            f'<a href="./">Back to {escape(ACCOUNT)}</a></p>'
        )
    return f'<div class="toolbar">{note}{render_search(account)}</div>'


def render_message(text: str) -> str:
    return f'<p class="search-message">{escape(text)}</p>'


def error_message(account: str, error: Exception) -> str:
    status = getattr(getattr(error, 'response', None), 'status_code', None)
    if status == 404:
        return f'No GitHub user named "{account}".'
    if status in (403, 429):
        return 'GitHub rate limit reached. Try again in a little while.'
    return f'Could not load repositories for "{account}" ({error}).'


def language_breakdown(repo: Repository) -> dict[str, float]:
    """Top languages by share; {} when unavailable (e.g. rate limited)."""
    try:
        languages = repo.languages
    except net.NeedFetch:
        return {}
    except net.HTTPError:
        return {}
    top = sorted(languages.items(), key=lambda item: item[1], reverse=True)
    return dict(top[:TOP_LANGUAGES])


LANGUAGE_COLORS = {
    'Python': '#3572a5', 'JavaScript': '#f1e05a', 'TypeScript': '#3178c6',
    'HTML': '#e34c26', 'CSS': '#663399', 'Shell': '#89e051', 'C': '#555555',
    'C++': '#f34b7d', 'C#': '#178600', 'Java': '#b07219', 'Go': '#00add8',
    'Rust': '#dea584', 'Kotlin': '#a97bff', 'Swift': '#f05138', 'Ruby': '#701516',
    'PHP': '#4f5d95', 'Dockerfile': '#384d54', 'Makefile': '#427819',
    'Jupyter Notebook': '#da5b0b', 'Lua': '#000080', 'Dart': '#00b4ab',
}


def name_hue(name: str) -> int:
    return sum(ord(ch) * 31 ** i for i, ch in enumerate(name)) % 360


def language_color(name: str) -> str:
    if name in LANGUAGE_COLORS:
        return LANGUAGE_COLORS[name]
    return f'hsl({name_hue(name)} 55% 55%)'


def render_languages(languages: dict[str, float]) -> str:
    bar = ''.join(
        f'<span style="--c:{language_color(name)};--w:{pct:g}%" title="{escape(name)} {pct:g}%"></span>'
        for name, pct in languages.items()
    )
    legend = ''.join(
        f'<li style="--c:{language_color(name)}">{escape(name)} <span>{pct:g}%</span></li>'
        for name, pct in languages.items()
    )
    return f'<div class="lang-bar" aria-hidden="true">{bar}</div><ul class="lang-legend">{legend}</ul>'


MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')


def icon(paths: str, view: int = 16) -> str:
    return f'<svg class="icon" viewBox="0 0 {view} {view}" aria-hidden="true">{paths}</svg>'


ICON_FORK = icon(
    '<circle cx="4" cy="3" r="1.6"/><circle cx="12" cy="3" r="1.6"/><circle cx="8" cy="13" r="1.6"/>'
    '<path d="M4 4.6v1.4a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2V4.6M8 8v3.4"/>'
)
ICON_STAR = icon('<path d="m8 1.8 1.9 3.9 4.3.6-3.1 3 .7 4.3L8 11.6l-3.8 2 .7-4.3-3.1-3 4.3-.6z"/>')
ICON_PIN = icon('<path d="M8 14.5s-4.5-4.2-4.5-7.8a4.5 4.5 0 0 1 9 0c0 3.6-4.5 7.8-4.5 7.8z"/><circle cx="8" cy="6.6" r="1.6"/>')
ICON_BRIEFCASE = icon('<rect x="1.8" y="4.5" width="12.4" height="9" rx="1.5"/><path d="M5.5 4.5V3a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1.5M1.8 8.5h12.4"/>')
ICON_MAIL = icon('<rect x="1.5" y="3" width="13" height="10" rx="1.5"/><path d="m2 4 6 5 6-5"/>')
ICON_LINK = icon('<path d="M6.5 9.5a3 3 0 0 0 4.2 0l2.3-2.3a3 3 0 0 0-4.2-4.2l-.8.8M9.5 6.5a3 3 0 0 0-4.2 0L3 8.8A3 3 0 0 0 7.2 13l.8-.8"/>')
ICON_GITHUB = icon(
    '<path class="fill" d="M8 .2a8 8 0 0 0-2.5 15.6c.4 0 .5-.2.5-.4v-1.5c-2.2.5-2.7-1-2.7-1-.4-.9-.9-1.2'
    '-.9-1.2-.7-.5.1-.5.1-.5.8.1 1.2.8 1.2.8.7 1.3 1.9.9 2.3.7.1-.5.3-.9.5-1.1-1.8-.2-3.6-.9-3.6-4 0-.9.3'
    '-1.6.8-2.1-.1-.2-.4-1 .1-2.1 0 0 .7-.2 2.2.8a7.6 7.6 0 0 1 4 0c1.5-1 2.2-.8 2.2-.8.4 1.1.2 1.9.1 2.1'
    '.5.6.8 1.3.8 2.1 0 3.1-1.9 3.8-3.7 4 .3.3.6.8.6 1.5v2.2c0 .2.1.5.6.4A8 8 0 0 0 8 .2z"/>'
)


def safe_url(url: str | None) -> str:
    url = (url or '').strip()
    if not url:
        return ''
    if '://' not in url:  # profile 'blog' is often just 'example.com'
        url = f'https://{url}'
    return url if url.startswith(('http://', 'https://')) else ''


def display_url(url: str) -> str:
    return url.split('://', 1)[1].rstrip('/').removeprefix('www.')


def month_year(timestamp: str) -> str:
    try:
        year, month = timestamp[:4], int(timestamp[5:7])
        return f'{MONTHS[month - 1]} {int(year)}'
    except (ValueError, IndexError):
        return ''


def load_profile(account: str) -> tuple[dict, list[dict]]:
    profile: dict = {}
    socials: list[dict] = []
    try:
        profile = fetch_profile(account)
    except (net.NeedFetch, net.HTTPError):
        pass
    try:
        socials = fetch_social_accounts(account)
    except (net.NeedFetch, net.HTTPError):
        pass
    return profile, socials


def render_contact(email: str) -> str:
    return (
        f'<button type="button" class="profile-link profile-link--primary" data-copy="{escape(email)}" '
        f'title="Copy {escape(email)}">{ICON_MAIL}Get in touch</button>'
    )


def render_profile(account: str, profile: dict, socials: list[dict]) -> str:
    login = profile.get('login') or account
    name = profile.get('name') or login
    github_url = safe_url(profile.get('html_url')) or f'https://github.com/{login}'

    avatar = safe_url(profile.get('avatar_url'))
    if avatar:
        sep = '&' if '?' in avatar else '?'
        picture = f'<img class="profile-avatar" src="{escape(avatar)}{sep}s=192" alt="" width="96" height="96">'
    else:
        picture = f'<span class="profile-avatar profile-avatar--initial" aria-hidden="true">{escape(name[:1].upper())}</span>'

    facts = []
    if profile.get('location'):
        facts.append(f'<li>{ICON_PIN}{escape(profile["location"])}</li>')
    if profile.get('company'):
        facts.append(f'<li>{ICON_BRIEFCASE}{escape(profile["company"])}</li>')

    links = []
    is_owner = login.lower() == ACCOUNT.lower()
    email = profile.get('email') or CONTACT_EMAIL
    if is_owner and email:
        links.append(render_contact(email))
    links.append(f'<a class="profile-link" href="{escape(github_url)}" rel="noopener">{ICON_GITHUB}GitHub</a>')

    seen = {github_url.rstrip('/').lower()}
    blog = safe_url(profile.get('blog'))
    extra = [('', blog)] if blog else []
    extra += [(item.get('provider', ''), safe_url(item.get('url'))) for item in socials]
    for provider, url in extra:
        if not url or url.rstrip('/').lower() in seen:
            continue
        seen.add(url.rstrip('/').lower())
        label = provider.capitalize() if provider and provider != 'generic' else display_url(url)
        if provider == 'linkedin':
            label = 'LinkedIn'
        links.append(f'<a class="profile-link" href="{escape(url)}" rel="noopener me">{ICON_LINK}{escape(label)}</a>')

    bio = f'<p class="profile-bio">{escape(profile["bio"])}</p>' if profile.get('bio') else ''
    handle = f'<p class="profile-handle">@{escape(login)}</p>' if name != login else ''
    facts_html = f'<ul class="profile-facts">{"".join(facts)}</ul>' if facts else ''
    return (
        '<header class="profile">'
        f'{picture}'
        '<div class="profile-text">'
        f'<h1>{escape(name)}</h1>{handle}{bio}{facts_html}'
        f'<nav class="profile-links" aria-label="Contact and profiles">{"".join(links)}</nav>'
        '</div>'
        '</header>'
    )


def render_repo(repo: Repository, languages: dict[str, float], featured: bool = False) -> str:
    title = escape(repo.name)
    if repo.html_url:
        title = f'<a class="repo-title" href="{escape(repo.html_url)}" rel="noopener">{title}</a>'
    badges = ''
    if repo.fork:
        badges += f'<span class="badge" title="Forked from another repository">{ICON_FORK}Fork</span>'
    if repo.archived:
        badges += '<span class="badge" title="Read-only, no longer maintained">Archived</span>'
    parts = [
        '<header class="repo-head">'
        f'<span class="repo-avatar" aria-hidden="true">{escape(repo.name[:1].upper())}</span>'
        f'<h3>{title}{badges}</h3>'
        '</header>'
    ]
    if repo.description:
        parts.append(f'<p class="repo-desc">{escape(repo.description)}</p>')
    if repo.topics:
        topics = ''.join(f'<li>{escape(topic)}</li>' for topic in repo.topics[:6])
        parts.append(f'<ul class="topics">{topics}</ul>')
    if languages:
        parts.append(render_languages(languages))
    elif repo.language:
        parts.append(render_languages({repo.language: 100}))

    meta = []
    if repo.stars:
        meta.append(f'<span title="Stars">{ICON_STAR}{repo.stars}</span>')
    if repo.forks_count:
        meta.append(f'<span title="Forks">{ICON_FORK}{repo.forks_count}</span>')
    updated = month_year(repo.pushed_at)
    if updated:
        meta.append(f'<span>Updated {updated}</span>')
    homepage = repo.homepage if (repo.homepage or '').startswith(('http://', 'https://')) else ''
    footer = f'<div class="repo-meta">{"".join(meta)}</div>' if meta else ''
    if homepage:
        footer += (
            f'<a class="repo-link" href="{escape(homepage)}" rel="noopener">'
            f'<span>{escape(display_url(homepage))}</span><span aria-hidden="true">↗</span></a>'
        )
    if footer:
        parts.append(f'<footer class="repo-foot">{footer}</footer>')

    cls = 'repo repo--featured' if featured else 'repo'
    return f'<li class="{cls}" style="--hue:{name_hue(repo.name)}">{"".join(parts)}</li>'


def pick_featured(account: str, repos: list[Repository]) -> list[Repository]:
    if account.lower() == ACCOUNT.lower() and FEATURED:
        by_name = {repo.name.lower(): repo for repo in repos}
        return [by_name[name.lower()] for name in FEATURED if name.lower() in by_name]
    own = [repo for repo in repos if not repo.fork and not repo.archived]
    own.sort(key=lambda repo: (repo.stars, repo.pushed_at), reverse=True)
    return own[:FEATURED_COUNT]


def render_section(title: str, items: list[str], cls: str) -> str:
    return (
        f'<section class="projects"><h2 class="section-title">{escape(title)}</h2>'
        f'<ul class="repos {cls}">{"".join(items)}</ul></section>'
    )


def render_repos(account: str) -> str:
    try:
        repos = fetch_repos(account)
    except net.HTTPError as error:
        return render_message(error_message(account, error))
    if not repos:
        return render_message(f'{account} has no public repositories.')

    repos.sort(key=lambda repo: repo.name.lower())
    featured = pick_featured(account, repos)
    rest = [repo for repo in repos if repo not in featured]

    html = ''
    if featured:
        cards = [render_repo(repo, language_breakdown(repo), featured=True) for repo in featured]
        html += render_section('Featured', cards, 'repos--featured')
    if rest:
        cards = [render_repo(repo, language_breakdown(repo)) for repo in rest]
        html += render_section('More projects' if featured else 'Projects', cards, '')
    return html


def main() -> None:
    account = requested_account()
    if not USERNAME.fullmatch(account):
        html = render_toolbar(account) + render_message(f'"{account}" is not a valid GitHub username.')
        print(json.dumps({'html': html}))
        return

    profile, socials = load_profile(account)
    try:
        body = render_repos(account)
    except net.NeedFetch:
        body = ''

    if net.MISSING:
        print(json.dumps({'need': net.MISSING}))
    else:
        print(json.dumps({'html': render_toolbar(account) + render_profile(account, profile, socials) + body}))


if __name__ == '__main__':
    main()
