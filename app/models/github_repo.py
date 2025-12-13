from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from typing import Optional

class GitHubRepo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner: str
    name: str
    url: str
    private: bool = Field(default=False)

class GitHubRepoUpdate(BaseModel):
    name: Optional[str] = None
    private: Optional[bool] = None