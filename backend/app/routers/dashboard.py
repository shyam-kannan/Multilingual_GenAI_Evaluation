from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ci_run import CIRun
from app.models.eval_run import EvalRun
from app.models.prompt import Prompt, PromptVersion

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    locales = ["en-US", "es-MX", "ar-SA", "ja-JP"]
    locale_stats = {}

    for locale in locales:
        runs = db.query(EvalRun).filter(EvalRun.locale == locale).all()
        if not runs:
            locale_stats[locale] = {
                "total_runs": 0,
                "pass_rate": 0.0,
                "avg_quality": 0.0,
                "avg_hallucination": 0.0,
            }
            continue

        passed_count = sum(1 for r in runs if r.overall_passed)
        locale_stats[locale] = {
            "total_runs": len(runs),
            "pass_rate": round(passed_count / len(runs), 4),
            "avg_quality": round(sum(r.quality_score for r in runs) / len(runs), 4),
            "avg_hallucination": round(
                sum(r.hallucination_score for r in runs) / len(runs), 4
            ),
        }

    total_runs = db.query(func.count(EvalRun.id)).scalar() or 0
    total_prompts = db.query(func.count(Prompt.id)).scalar() or 0

    recent_runs = (
        db.query(EvalRun)
        .order_by(EvalRun.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "locale_stats": locale_stats,
        "total_runs": total_runs,
        "total_prompts": total_prompts,
        "recent_runs": [
            {
                "id": str(r.id),
                "locale": r.locale,
                "quality_score": r.quality_score,
                "hallucination_score": r.hallucination_score,
                "overall_passed": r.overall_passed,
                "created_at": r.created_at.isoformat(),
            }
            for r in recent_runs
        ],
    }


@router.get("/prompts/{prompt_id}/history")
def prompt_history(prompt_id: UUID, db: Session = Depends(get_db)):
    versions = (
        db.query(PromptVersion)
        .filter(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version)
        .all()
    )

    history = []
    for version in versions:
        runs = (
            db.query(EvalRun)
            .filter(EvalRun.prompt_version_id == version.id)
            .all()
        )

        locale_scores = {}
        for run in runs:
            if run.locale not in locale_scores:
                locale_scores[run.locale] = {"quality": [], "hallucination": []}
            locale_scores[run.locale]["quality"].append(run.quality_score)
            locale_scores[run.locale]["hallucination"].append(run.hallucination_score)

        avg_scores = {}
        for locale, scores in locale_scores.items():
            avg_scores[locale] = {
                "avg_quality": round(sum(scores["quality"]) / len(scores["quality"]), 4),
                "avg_hallucination": round(
                    sum(scores["hallucination"]) / len(scores["hallucination"]), 4
                ),
                "run_count": len(scores["quality"]),
            }

        history.append({
            "version": version.version,
            "version_id": str(version.id),
            "labels": version.labels,
            "is_active": version.is_active,
            "created_at": version.created_at.isoformat(),
            "locale_scores": avg_scores,
        })

    return {"prompt_id": str(prompt_id), "history": history}


@router.get("/ci-history")
def ci_history(
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    runs = (
        db.query(CIRun)
        .order_by(CIRun.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(r.id),
            "prompt_id": str(r.prompt_id),
            "candidate_version_id": str(r.candidate_version_id),
            "baseline_version_id": str(r.baseline_version_id) if r.baseline_version_id else None,
            "status": r.status,
            "regressions": r.regressions,
            "details": r.details,
            "created_at": r.created_at.isoformat(),
        }
        for r in runs
    ]
