"""Base class for native tool classes without LangChain dependencies."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class BaseTool(BaseModel):
    """Native tool wrapper replacing langchain_core.tools.BaseTool."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = ""
    description: str = ""
    args_schema: type[BaseModel] | None = None

    async def _arun(self, *args: Any, **kwargs: Any) -> str:
        raise NotImplementedError

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("Use async execution (_arun)")
