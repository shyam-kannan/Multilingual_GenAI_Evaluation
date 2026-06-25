from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.golden_set import GoldenExample
from app.models.prompt import Prompt
from app.schemas.golden_set import GoldenExampleCreate, GoldenExampleOut, GoldenExampleUpdate

router = APIRouter(prefix="/api/golden-sets", tags=["golden-sets"])


@router.post("", response_model=GoldenExampleOut, status_code=201)
def create_golden_example(body: GoldenExampleCreate, db: Session = Depends(get_db)):
    prompt = db.query(Prompt).filter(Prompt.id == body.prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    example = GoldenExample(
        prompt_id=body.prompt_id,
        locale=body.locale,
        input_text=body.input_text,
        expected_output=body.expected_output,
    )
    db.add(example)
    db.commit()
    db.refresh(example)
    return example


@router.get("", response_model=list[GoldenExampleOut])
def list_golden_examples(
    prompt_id: Optional[UUID] = Query(None),
    locale: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(GoldenExample)
    if prompt_id:
        query = query.filter(GoldenExample.prompt_id == prompt_id)
    if locale:
        query = query.filter(GoldenExample.locale == locale)
    return query.order_by(GoldenExample.created_at.desc()).all()


@router.put("/{example_id}", response_model=GoldenExampleOut)
def update_golden_example(
    example_id: UUID, body: GoldenExampleUpdate, db: Session = Depends(get_db)
):
    example = db.query(GoldenExample).filter(GoldenExample.id == example_id).first()
    if not example:
        raise HTTPException(status_code=404, detail="Golden example not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(example, key, value)

    db.commit()
    db.refresh(example)
    return example


@router.delete("/{example_id}", status_code=204)
def delete_golden_example(example_id: UUID, db: Session = Depends(get_db)):
    example = db.query(GoldenExample).filter(GoldenExample.id == example_id).first()
    if not example:
        raise HTTPException(status_code=404, detail="Golden example not found")

    db.delete(example)
    db.commit()
