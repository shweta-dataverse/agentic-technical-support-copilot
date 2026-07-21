"""Loads versioned prompts from prompts/*.yaml. The version is logged with every call."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel


def _prompts_dir() -> Path:
    """Find the prompts folder in dev and in the container.

    Order: COPILOT_PROMPTS_DIR env, then ./prompts relative to the working
    directory (repo root in dev, /app in the container), then the source tree.
    """
    env = os.environ.get("COPILOT_PROMPTS_DIR")
    if env:
        return Path(env)
    cwd_prompts = Path("prompts")
    if cwd_prompts.is_dir():
        return cwd_prompts
    return Path(__file__).resolve().parents[3] / "prompts"


PROMPTS_DIR = _prompts_dir()


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
