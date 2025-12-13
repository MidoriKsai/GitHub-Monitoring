from sqlmodel import SQLModel, Field
from typing import Optional

class GitHubRepo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner: str
    name: str
    url: str
    private: bool = False

class GitHubRepoUpdate(SQLModel):
    name: Optional[str]
    private: Optional[bool]

class GitHubRepoCreate(SQLModel):
    name: str
    private: bool = True