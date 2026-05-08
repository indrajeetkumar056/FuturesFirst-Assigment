from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=20_000)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=10_000)
    filters: dict[str, str] | None = Field(default=None, max_length=32)
    history: list[ChatMessage] | None = Field(default=None, max_length=50)

    @field_validator("question")
    @classmethod
    def question_stripped(cls, v: str) -> str:
        q = v.strip()
        if not q:
            raise ValueError("question cannot be only whitespace")
        return q

    @field_validator("filters", mode="before")
    @classmethod
    def filters_keys_strings(cls, v: object) -> object:
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("filters must be an object mapping string keys to string values")
        out: dict[str, str] = {}
        for k, val in v.items():
            if not isinstance(k, str) or not k.strip():
                raise ValueError("filter keys must be non-empty strings")
            if not isinstance(val, str):
                raise ValueError("filter values must be strings")
            out[k.strip()] = val.strip()
        return out


class ToolTrace(BaseModel):
    name: str
    input: dict
    output_summary: str


class DocumentCitation(BaseModel):
    chunk_id: int
    source_name: str
    page_number: int | None = None
    section: str | None = None
    score: float
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    tool_trace: list[ToolTrace]
    chart: dict | None = None
    citations: list[DocumentCitation] = Field(default_factory=list)
    sql_tables_used: list[str] = Field(default_factory=list)
    route_kind: str | None = None

