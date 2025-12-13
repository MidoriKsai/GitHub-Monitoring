# app/services/parser.py
import asyncio
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright

def get_repos_sync(username: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://github.com/{username}?tab=repositories")
        repo_elements = page.query_selector_all('h3 a[itemprop="name codeRepository"]')
        repos = []
        for el in repo_elements:
            name = el.inner_text().strip()
            link = f"https://github.com/{username}/{name}"
            repos.append({"name": name, "link": link})
        browser.close()
    return repos

async def get_repos(username: str):
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, get_repos_sync, username)
