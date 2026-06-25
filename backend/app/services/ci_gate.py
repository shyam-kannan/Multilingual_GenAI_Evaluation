from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.ci_run import CIRun
from app.models.eval_run import EvalRun
from app.models.golden_set import GoldenExample
from app.models.prompt import Prompt, PromptVersion
from app.services import judge, moderator, world_readiness
from app.services.llm import generate


def _get_baseline_version(db: Session, prompt_id: UUID) -> PromptVersion | None:
    return (
        db.query(PromptVersion)
        .filter(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.labels.contains("production"),
        )
        .order_by(PromptVersion.version.desc())
        .first()
    )


def _get_baseline_version_sqlite(db: Session, prompt_id: UUID) -> PromptVersion | None:
    versions = (
        db.query(PromptVersion)
        .filter(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version.desc())
        .all()
    )
    for v in versions:
        if isinstance(v.labels, list) and "production" in v.labels:
            return v
    return None


def _get_baseline_scores(db: Session, version_id: UUID, locale: str) -> dict | None:
    runs = (
        db.query(EvalRun)
        .filter(EvalRun.prompt_version_id == version_id, EvalRun.locale == locale)
        .all()
    )
    if not runs:
        return None
    avg_quality = sum(r.quality_score for r in runs) / len(runs)
    avg_hallucination = sum(r.hallucination_score for r in runs) / len(runs)
    return {
        "quality": round(avg_quality, 4),
        "hallucination": round(avg_hallucination, 4),
        "run_count": len(runs),
    }


def _run_eval(
    db: Session, version: PromptVersion, input_text: str, locale: str
) -> EvalRun:
    llm_output = generate(version.content, input_text, locale)

    quality = judge.score_quality(version.content, input_text, llm_output, locale)
    hallucination = judge.score_hallucination(
        version.content, input_text, llm_output, locale
    )
    moderation_result = moderator.check_moderation(llm_output, locale)
    wr_result = world_readiness.validate(llm_output, locale)

    quality_passed = quality["score"] >= settings.quality_threshold
    hallucination_passed = hallucination["score"] <= settings.hallucination_threshold
    overall_passed = (
        quality_passed
        and hallucination_passed
        and moderation_result["passed"]
        and wr_result["passed"]
    )

    eval_run = EvalRun(
        prompt_version_id=version.id,
        locale=locale,
        input_text=input_text,
        llm_output=llm_output,
        quality_score=quality["score"],
        quality_reasoning=quality["reasoning"],
        hallucination_score=hallucination["score"],
        hallucination_reasoning=hallucination["reasoning"],
        moderation_passed=moderation_result["passed"],
        moderation_reasoning=moderation_result["reasoning"],
        world_readiness_passed=wr_result["passed"],
        world_readiness_details=wr_result,
        overall_passed=overall_passed,
    )
    db.add(eval_run)
    db.commit()
    db.refresh(eval_run)
    return eval_run


def run_ci_check(
    db: Session,
    prompt: Prompt,
    candidate_version: PromptVersion,
    locales: list[str],
) -> CIRun:
    try:
        baseline = _get_baseline_version_sqlite(db, prompt.id)
    except Exception:
        baseline = None

    if baseline and baseline.id == candidate_version.id:
        baseline = None

    golden_examples = (
        db.query(GoldenExample)
        .filter(
            GoldenExample.prompt_id == prompt.id,
            GoldenExample.locale.in_(locales),
        )
        .all()
    )

    regressions = []
    locale_scores = {}

    for locale in locales:
        locale_goldens = [g for g in golden_examples if g.locale == locale]
        if not locale_goldens:
            locale_scores[locale] = {"status": "skipped", "reason": "no golden examples"}
            continue

        candidate_runs = []
        for golden in locale_goldens:
            run = _run_eval(db, candidate_version, golden.input_text, locale)
            candidate_runs.append(run)

        avg_quality = sum(r.quality_score for r in candidate_runs) / len(candidate_runs)
        avg_hallucination = sum(r.hallucination_score for r in candidate_runs) / len(
            candidate_runs
        )

        locale_scores[locale] = {
            "quality": round(avg_quality, 4),
            "hallucination": round(avg_hallucination, 4),
            "run_count": len(candidate_runs),
            "all_passed": all(r.overall_passed for r in candidate_runs),
        }

        if baseline:
            baseline_scores = _get_baseline_scores(db, baseline.id, locale)
            if baseline_scores:
                quality_delta = baseline_scores["quality"] - avg_quality
                hall_delta = avg_hallucination - baseline_scores["hallucination"]

                if quality_delta > settings.regression_delta:
                    regressions.append({
                        "locale": locale,
                        "metric": "quality",
                        "baseline": baseline_scores["quality"],
                        "candidate": round(avg_quality, 4),
                        "delta": round(-quality_delta, 4),
                    })

                if hall_delta > settings.regression_delta:
                    regressions.append({
                        "locale": locale,
                        "metric": "hallucination",
                        "baseline": baseline_scores["hallucination"],
                        "candidate": round(avg_hallucination, 4),
                        "delta": round(hall_delta, 4),
                    })

    status = "failed" if regressions else "passed"

    ci_run = CIRun(
        prompt_id=prompt.id,
        candidate_version_id=candidate_version.id,
        baseline_version_id=baseline.id if baseline else None,
        status=status,
        regressions=regressions,
        details=locale_scores,
    )
    db.add(ci_run)
    db.commit()
    db.refresh(ci_run)
    return ci_run
