from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

_FIXTURES = Path(__file__).parent / "fixtures"


@lru_cache
def _load(name: str) -> Any:
    with open(_FIXTURES / name) as f:
        return json.load(f)


def get_demo_state() -> dict:
    return deepcopy(_load("demo_state.json"))


def get_demo_job(job_id: str) -> dict | None:
    payload = _load("demo_jobs.json").get(job_id)
    return deepcopy(payload) if payload else None


def get_demo_jobs() -> list[dict]:
    return [deepcopy(item) for item in _load("demo_jobs.json").values()]


def get_demo_intent(intent_id: str) -> dict | None:
    payload = _load("demo_intents.json").get(intent_id)
    return deepcopy(payload) if payload else None


def get_demo_reviews() -> list[dict]:
    return deepcopy(_load("demo_reviews.json"))


def get_demo_compliance() -> dict:
    return deepcopy(_load("demo_compliance.json"))
