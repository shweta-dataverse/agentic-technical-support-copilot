# shared FastAPI dependencies: settings, api-key auth, llm provider.

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from copilot.config import Settings, get_settings
from copilot.llm.providers import LLMProvider, get_llm_provider

SettingsDep = Annotated[Settings, Depends(get_settings)]
LLMProviderDep = Annotated[LLMProvider, Depends(get_llm_provider)]


def require_api_key(
    settings: SettingsDep,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing API key",
        )
