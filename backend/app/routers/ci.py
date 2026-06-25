from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.prompt import Prompt, PromptVersion
from app.schemas.ci import CICheckRequest, CICheckResponse
from app.services.ci_gate import run_ci_check

router = APIRouter(prefix="/api/ci", tags=["ci"])


@router.post("/check", response_model=CICheckResponse)
def ci_check(body: CICheckRequest, db: Session = Depends(get_db)):
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

    ci_run = run_ci_check(db, prompt, version, body.locales)

    return CICheckResponse(
        ci_run_id=ci_run.id,
        passed=ci_run.status == "passed",
        status=ci_run.status,
        regressions=ci_run.regressions,
        details=ci_run.details,
    )
