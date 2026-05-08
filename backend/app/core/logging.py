from __future__ import annotations

import logging
import os


def configure_logging(level_name: str | None = None) -> None:
    """
    Root logging for the app. Uvicorn keeps its own loggers; this sets the default `logging` tree.
    """
    name = (level_name or os.getenv("LOG_LEVEL") or "INFO").upper()
    level = getattr(logging, name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        force=True,
    )
    logging.getLogger(__name__).debug("logging configured at %s", logging.getLevelName(level))
