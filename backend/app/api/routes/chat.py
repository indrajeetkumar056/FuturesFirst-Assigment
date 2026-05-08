from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.agents.orchestrator import run_tool_plan
from app.api.deps import get_principal
from app.core.security import Principal
from app.memory_store import get_demo_store
from app.schemas.chat import ChatRequest, ChatResponse, ToolTrace
from app.services.llm_client import chat_completion, get_client

log = logging.getLogger("app.chat")

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, principal: Principal = Depends(get_principal)) -> ChatResponse:
    log.info(
        "chat start subject=%s question_len=%s filters=%s",
        principal.subject,
        len(req.question),
        bool(req.filters),
    )
    store = get_demo_store()
    orch = await run_tool_plan(store, question=req.question)

    try:
        _client, model, provider = get_client()
    except ValueError as e:
        log.warning("chat LLM configuration error: %s", e)
        raise HTTPException(
            status_code=503,
            detail="LLM is not configured (check LLM_PROVIDER and API keys in .env).",
        ) from e

    orch.tool_trace.append(
        ToolTrace(
            name="llm_provider",
            input={"provider": provider, "model": model},
            output_summary="configured",
        )
    )

    context = "\n\n".join(orch.context_blocks) if orch.context_blocks else "No tool context yet."
    citation_hint = ""
    if orch.citations:
        citation_hint = "\nCite chunk ids like [123] when quoting documents."

    system = (
        "You are an internal analytics assistant. "
        "Use ONLY the tool-provided context below (structured analytics from CSV data and document excerpts from PDFs). "
        "Do not invent numbers. If unsupported, say what data might be missing. "
        "Give a short executive summary, then bullets for evidence, then recommendations when asked."
    )
    user = (
        f"User: {principal.subject}\n"
        f"Route (router): {orch.route_kind}\n"
        f"Question: {req.question}\n\n"
        f"{context}\n"
        f"{citation_hint}"
    )

    try:
        answer = chat_completion(system=system, user=user).strip()
    except ValueError as e:
        log.warning("chat LLM configuration error: %s", e)
        raise HTTPException(
            status_code=503,
            detail="LLM is not configured (check LLM_PROVIDER and API keys in .env).",
        ) from e
    except Exception as e:
        log.exception("chat LLM request failed subject=%s", principal.subject)
        raise HTTPException(
            status_code=502,
            detail="Upstream LLM request failed. Retry or verify provider status.",
        ) from e

    log.info("chat done subject=%s answer_len=%s", principal.subject, len(answer))
    return ChatResponse(
        answer=answer,
        sources=orch.sources,
        tool_trace=orch.tool_trace,
        chart=orch.chart,
        citations=orch.citations,
        sql_tables_used=orch.sql_tables_used,
        route_kind=orch.route_kind,
    )
