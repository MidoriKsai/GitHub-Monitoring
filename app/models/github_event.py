from sqlmodel import SQLModel, Field
from typing import Optional

class GitHubCommit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repo: str
    sha: str
    message: str
    url: str

class GitHubIssue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repo: str
    issue_number: int
    title: str
    state: str
    url: str

class GitHubRelease(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repo: str
    tag_name: str
    name: Optional[str]
    url: str
