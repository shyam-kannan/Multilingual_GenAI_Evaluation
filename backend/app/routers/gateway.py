from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.eval_run import EvalRun
from app.models.prompt import Prompt, PromptVersion
from app.schemas.eval_run import GatewayRunResponse
from app.schemas.gateway import GatewayRunRequest
from app.services import judge, moderator, world_readiness
from app.services.llm import generate

router = APIRouter(prefix="/api/gateway", tags=["gateway"])


@router.post("/run", response_model=GatewayRunResponse)
def run_gateway(body: GatewayRunRequest, db: Session = Depends(get_db)):
    prompt = db.query(Prompt).filter(Prompt.name == body.prompt_name).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    if body.version_id:
        version = (
            db.query(PromptVersion)
            .filter(
                PromptVersion.id == body.version_id,
                PromptVersion.prompt_id == prompt.id,
            )
            .first()
        )
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
    else:
        version = (
            db.query(PromptVersion)
            .filter(
                PromptVersion.prompt_id == prompt.id,
                PromptVersion.is_active == True,
            )
            .first()
        )
        if not version:
            raise HTTPException(status_code=404, detail="No active version found")

    llm_output = generate(version.content, body.input, body.locale)

    quality = judge.score_quality(version.content, body.input, llm_output, body.locale)
    hallucination = judge.score_hallucination(
        version.content, body.input, llm_output, body.locale
    )
    moderation_result = moderator.check_moderation(llm_output, body.locale)

    wr_result = world_readiness.validate(llm_output, body.locale)
    world_readiness_passed = wr_result["passed"]
    world_readiness_details = wr_result

    quality_passed = quality["score"] >= settings.quality_threshold
    hallucination_passed = hallucination["score"] <= settings.hallucination_threshold
    overall_passed = (
        quality_passed
        and hallucination_passed
        and moderation_result["passed"]
        and world_readiness_passed
    )

    eval_run = EvalRun(
        prompt_version_id=version.id,
        locale=body.locale,
        input_text=body.input,
        llm_output=llm_output,
        quality_score=quality["score"],
        quality_reasoning=quality["reasoning"],
        hallucination_score=hallucination["score"],
        hallucination_reasoning=hallucination["reasoning"],
        moderation_passed=moderation_result["passed"],
        moderation_reasoning=moderation_result["reasoning"],
        world_readiness_passed=world_readiness_passed,
        world_readiness_details=world_readiness_details,
        overall_passed=overall_passed,
    )
    db.add(eval_run)
    db.commit()
    db.refresh(eval_run)

    return GatewayRunResponse(
        eval_run_id=eval_run.id,
        llm_output=llm_output,
        quality_score=quality["score"],
        hallucination_score=hallucination["score"],
        moderation_passed=moderation_result["passed"],
        world_readiness_passed=world_readiness_passed,
        overall_passed=overall_passed,
        details={
            "quality": quality,
            "hallucination": hallucination,
            "moderation": moderation_result,
            "world_readiness": {
                "passed": world_readiness_passed,
                "details": world_readiness_details,
            },
        },
    )
