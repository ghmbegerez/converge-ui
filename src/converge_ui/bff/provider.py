from __future__ import annotations

from typing import Any

from converge_ui.bff.cache import SnapshotCache
from converge_ui.bff.demo_data import (
    get_demo_compliance,
    get_demo_intent,
    get_demo_job,
    get_demo_jobs,
    get_demo_reviews,
    get_demo_state,
)
from converge_ui.bff.helpers import review_summary_from_items
from converge_ui.clients.converge_client import ConvergeClient
from converge_ui.clients.orchestrator_client import OrchestratorClient
from converge_ui.config.settings import Settings
from converge_ui.observability import stats


class DataProvider:
    def __init__(
        self,
        settings: Settings,
        *,
        orchestrator: OrchestratorClient,
        converge: ConvergeClient,
        cache: SnapshotCache,
    ) -> None:
        self.settings = settings
        self.orchestrator = orchestrator
        self.converge = converge
        self.cache = cache

    def resolve_state(self) -> dict[str, Any]:
        real_state = None if self.settings.data_mode == "demo" else self.orchestrator.state()
        if real_state is not None:
            stats().inc("provider.state.real")
            payload = {"payload": real_state, "source": "real"}
            self.cache.set("state", payload)
            return payload
        cached = self.cache.get("state")
        if cached is not None and self.settings.data_mode != "demo":
            stats().inc("provider.state.stale_cache")
            payload = dict(cached.payload)
            payload["source"] = "stale-cache"
            return payload
        stats().inc("provider.state.demo")
        return {"payload": get_demo_state(), "source": "demo"}

    def get_job_payload(self, job_id: str) -> tuple[dict[str, Any] | None, str]:
        orchestrator_job = self.orchestrator.get_job(job_id)
        if orchestrator_job is not None:
            stats().inc("provider.job.real")
            return orchestrator_job, "real"
        demo_job = get_demo_job(job_id)
        if demo_job is not None:
            stats().inc("provider.job.demo")
            return demo_job, "demo"
        stats().inc("provider.job.miss")
        return None, "demo"

    def get_reviews_payload(self) -> tuple[list[dict[str, Any]], dict[str, Any] | None, str]:
        reviews = [] if self.settings.data_mode == "demo" else self.converge.reviews()
        summary = None if self.settings.data_mode == "demo" else self.converge.reviews_summary()
        if reviews or summary is not None:
            stats().inc("provider.reviews.real")
            return reviews, summary, "real"
        reviews = get_demo_reviews()
        stats().inc("provider.reviews.demo")
        return reviews, review_summary_from_items(reviews), "demo"

    def get_compliance_payload(self) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str]:
        report = None if self.settings.data_mode == "demo" else self.converge.compliance_report()
        alerts = [] if self.settings.data_mode == "demo" else self.converge.compliance_alerts()
        if report is not None or alerts:
            stats().inc("provider.compliance.real")
            return report, alerts, "real"
        report = get_demo_compliance()
        stats().inc("provider.compliance.demo")
        return report, report.get("alerts", []), "demo"

    def get_intent_bundle(self, intent_id: str | None) -> dict[str, Any] | None:
        if not intent_id:
            return None
        intent = None if self.settings.data_mode == "demo" else self.converge.get_intent(intent_id)
        events = [] if self.settings.data_mode == "demo" else self.converge.get_intent_events(intent_id)
        risk_review = None if self.settings.data_mode == "demo" else self.converge.get_risk_review(intent_id)
        reviews = [] if self.settings.data_mode == "demo" else self.converge.reviews(intent_id=intent_id)
        review_summary = None if self.settings.data_mode == "demo" else self.converge.reviews_summary()
        compliance_report = None if self.settings.data_mode == "demo" else self.converge.compliance_report()
        if intent is not None:
            stats().inc("provider.intent.real")
            return {
                "intent": intent,
                "events": events,
                "risk_review": risk_review,
                "reviews": reviews,
                "review_summary": review_summary,
                "compliance_report": compliance_report,
                "data_source": "real",
            }
        demo = get_demo_intent(intent_id)
        if demo is not None:
            stats().inc("provider.intent.demo")
            return {
                "intent": demo["intent"],
                "events": demo["events"],
                "risk_review": demo["risk_review"],
                "reviews": demo.get("reviews", []),
                "review_summary": demo.get("review_summary"),
                "compliance_report": demo.get("compliance_report"),
                "data_source": "demo",
            }
        stats().inc("provider.intent.miss")
        return None

    def seed_jobs_for_source(self, source: str) -> dict[str, dict[str, Any]]:
        if source == "real":
            return {}
        return {item["job"]["id"]: item for item in get_demo_jobs()}
