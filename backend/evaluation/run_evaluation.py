import asyncio
import json
import statistics
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.models.entities import User
from app.rag.access import build_access_scope
from app.rag.agent import hr_agent
from app.schemas.auth import CurrentUser

DATASET = Path(__file__).with_name("golden_dataset.json")


async def run() -> None:
    cases = json.loads(DATASET.read_text())
    results = []
    async with SessionLocal() as db:
        for case in cases:
            user = await db.scalar(
                select(User).options(selectinload(User.employee)).where(User.email == case["user"])
            )
            if not user:
                raise RuntimeError(f"Seed user missing: {case['user']}")
            current = CurrentUser(
                id=user.id, email=user.email, full_name=user.full_name, role=user.role.value,
                department_id=user.employee.department_id if user.employee else None,
                authz_version=user.authz_version,
            )
            output = await hr_agent.run(db, build_access_scope(current), case["question"], [])
            answer = output["answer"].lower()
            abstained = "couldn't find" in answer or "contact hr" in answer
            terms = case["expected_terms"]
            citations = output.get("citations", [])
            expected_source = case.get("expected_source")
            matching_sources = [
                item for item in citations if item["filename"] == expected_source
            ] if expected_source else []
            results.append({
                "id": case["id"], "answer": output["answer"],
                "term_recall": sum(term.lower() in answer for term in terms) / max(len(terms), 1),
                "retrieval_hit": (expected_source is None) or bool(matching_sources),
                "context_precision_proxy": (
                    len(matching_sources) / len(citations) if citations else int(expected_source is None)
                ),
                "citation_valid": (not case["must_cite"]) or bool(citations),
                "grounded": output["trace"].get("grounded", False),
                "abstention_correct": abstained == case["must_abstain"],
                "latency_ms": output["trace"]["latency_ms"],
                "token_usage": output["trace"].get("token_usage", {}),
            })
    summary = {
        "cases": len(results),
        "mean_term_recall": statistics.mean(item["term_recall"] for item in results),
        "retrieval_hit_rate": statistics.mean(item["retrieval_hit"] for item in results),
        "context_precision_proxy": statistics.mean(
            item["context_precision_proxy"] for item in results
        ),
        "citation_validity": statistics.mean(item["citation_valid"] for item in results),
        "groundedness": statistics.mean(item["grounded"] for item in results),
        "abstention_accuracy": statistics.mean(item["abstention_correct"] for item in results),
        "p50_latency_ms": statistics.median(item["latency_ms"] for item in results),
        "details": results,
    }
    Path("evaluation-results.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(run())
