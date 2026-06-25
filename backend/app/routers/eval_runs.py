from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.eval_run import EvalRun
from app.schemas.eval_run import EvalRunOut

router = APIRouter(prefix="/api/eval-runs", tags=["eval-runs"])


@router.get("", response_model=list[EvalRunOut])
def list_eval_runs(
    prompt_version_id: Optional[UUID] = Query(None),
    locale: Optional[str] = Query(None),
    passed: Optional[bool] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(EvalRun)
    if prompt_version_id:
        query = query.filter(EvalRun.prompt_version_id == prompt_version_id)
    if locale:
        query = query.filter(EvalRun.locale == locale)
    if passed is not None:
        query = query.filter(EvalRun.overall_passed == passed)
    return query.order_by(EvalRun.created_at.desc()).limit(limit).all()


@router.get("/{eval_run_id}", response_model=EvalRunOut)
def get_eval_run(eval_run_id: UUID, db: Session = Depends(get_db)):
    run = db.query(EvalRun).filter(EvalRun.id == eval_run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return run
