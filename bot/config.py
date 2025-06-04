from dataclasses import dataclass, field
from typing import List
import json
from pathlib import Path


@dataclass
class Config:
    token: str
    default_language: str = 'ru'
    cities: List[str] = field(default_factory=list)
    followup_delay: int = 120  # seconds
    db_url: str = 'postgresql+asyncpg://user:password@localhost/hitchhiker'

    @classmethod
    def load(cls, path: str | Path) -> 'Config':
        data = json.loads(Path(path).read_text())
        return cls(**data)
