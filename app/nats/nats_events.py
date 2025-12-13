import asyncio
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.db import get_db
from app.models.github_repo import GitHubRepo
from app.models.github_event import GitHubCommit, GitHubIssue, GitHubRelease
from nats.aio.client import Client as NATS
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")



async def fetch_github_data(db: AsyncSession):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    async with httpx.AsyncClient() as client:
        # Получаем все репозитории из БД
        result = await db.execute(select(GitHubRepo))
        repos = result.scalars().all()

        for repo in repos:
            full_name = f"{repo.owner}/{repo.name}"

            # ----------------------------
            # Получаем последние коммиты
            # ----------------------------
            commits_resp = await client.get(f"https://api.github.com/repos/{full_name}/commits", headers=headers)
            if commits_resp.status_code == 200:
                commits = commits_resp.json()
                for c in commits:
                    commit = GitHubCommit(
                        repo=full_name,
                        sha=c["sha"],
                        message=c["commit"]["message"],
                        url=c["html_url"]
                    )
                    db.add(commit)

            # ----------------------------
            # Получаем открытые issues
            # ----------------------------
            issues_resp = await client.get(f"https://api.github.com/repos/{full_name}/issues", headers=headers, params={"state": "open"})
            if issues_resp.status_code == 200:
                issues = issues_resp.json()
                for i in issues:
                    if "pull_request" not in i:  # исключаем PR
                        issue = GitHubIssue(
                            repo=full_name,
                            issue_number=i["number"],
                            title=i["title"],
                            state=i["state"],
                            url=i["html_url"]
                        )
                        db.add(issue)

            # ----------------------------
            # Получаем последние релизы
            # ----------------------------
            releases_resp = await client.get(f"https://api.github.com/repos/{full_name}/releases", headers=headers)
            if releases_resp.status_code == 200:
                releases = releases_resp.json()
                for r in releases:
                    release = GitHubRelease(
                        repo=full_name,
                        tag_name=r["tag_name"],
                        name=r.get("name"),
                        url=r["html_url"]
                    )
                    db.add(release)

        # Сохраняем все изменения
        await db.commit()

        # ----------------------------
        # Публикуем событие в NATS
        # ----------------------------
        nc = NATS()
        await nc.connect(NATS_URL)
        await nc.publish("github.updates", b"GitHub data synced")
        await nc.flush()
        await nc.close()