import asyncio
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright

def get_repos_sync(username: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(
            f"https://github.com/{username}?tab=repositories",
            wait_until="networkidle"
        )

        repo_elements = page.query_selector_all(
            'li[itemprop="owns"] h3 a'
        )

        repos = []
        for el in repo_elements:
            name = el.inner_text().strip()
            href = el.get_attribute("href")

            parent_li = el.evaluate_handle("el => el.closest('li')")
            private_span = parent_li.query_selector("span.Label--red")
            private = bool(private_span)

            repos.append({
                "owner": username,
                "name": name,
                "url": f"https://github.com{href}",
                "private": private
            })

        browser.close()
        return repos

async def get_repos(username: str):
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, get_repos_sync, username)
