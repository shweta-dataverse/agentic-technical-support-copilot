"""Versioned prompt artifacts.

Prompts live in prompts/*.yaml as YAML front-matter (id, version, changelog)
followed by the user-message template. The version is logged with every LLM
call, so any generation can be traced to the exact prompt text that produced
it. Prompts change only via pull request.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"


class Prompt(BaseModel):
    id: str
    version: str
    system: str
    template: str

    def render(self, **kwargs: str) -> str:
        return self.template.format(**kwargs)


@lru_cache
def load_prompt(name: str) -> Prompt:
    raw = (PROMPTS_DIR / f"{name}.yaml").read_text(encoding="utf-8")
    _, front_matter, body = raw.split("---", 2)
    meta = yaml.safe_load(front_matter)
    return Prompt(
        id=str(meta["id"]),
        version=str(meta["version"]),
        system=str(meta["system"]).strip(),
        template=body.strip(),
    )
