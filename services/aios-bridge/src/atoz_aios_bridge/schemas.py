"""Pydantic schemas for the AI OS Bridge API (M10 Step 2 dispatch).

The bridge accepts an internal dispatch envelope from the automation
service (``job_id`` + ``contract`` + business ``request``) and maps it to
the frozen ``AIOS.Job.Request`` contract. The envelope carries business
references only — never prompts or generated-content internals.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BridgeJobRequest(BaseModel):
    """Business-layer dispatch envelope (Website → Bridge → AI OS)."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1, max_length=128)
    contract: str = Field(
        pattern="^(content-intake|seo-metadata|pinterest-assets|analytics-insights)$"
    )
    niche_id: str = Field(min_length=1, max_length=36)
    request: dict[str, Any] = Field(default_factory=dict)


class BridgeJobOut(BaseModel):
    """Dispatch result: the AI OS job id + the request id used."""

    aios_job_id: str
    request_id: str
    contract: str
    job_type: str
