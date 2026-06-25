import difflib
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.prompt import Prompt, PromptVersion
from app.schemas.prompt import (
    DiffOut,
    LabelsUpdate,
    PromptCreate,
    PromptDetailOut,
    PromptOut,
    PromptVersionCreate,
    PromptVersionOut,
)
from app.utils.hashing import content_hash

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.post("", response_model=PromptOut, status_code=201)
def create_prompt(body: PromptCreate, db: Session = Depends(get_db)):
    existing = db.query(Prompt).filter(Prompt.name == body.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Prompt name already exists")
    prompt = Prompt(name=body.name)
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.get("", response_model=list[PromptOut])
def list_prompts(db: Session = Depends(get_db)):
    return db.query(Prompt).order_by(Prompt.created_at.desc()).all()


@router.get("/{prompt_id}", response_model=PromptDetailOut)
def get_prompt(prompt_id: UUID, db: Session = Depends(get_db)):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.post("/{prompt_id}/versions", response_model=PromptVersionOut, status_code=201)
def create_version(
    prompt_id: UUID, body: PromptVersionCreate, db: Session = Depends(get_db)
):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    hash_val = content_hash(body.content)
    duplicate = (
        db.query(PromptVersion)
        .filter(PromptVersion.prompt_id == prompt_id, PromptVersion.content_hash == hash_val)
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate content matches version {duplicate.version}",
        )

    max_version = (
        db.query(func.max(PromptVersion.version))
        .filter(PromptVersion.prompt_id == prompt_id)
        .scalar()
    ) or 0

    is_first = max_version == 0
    version = PromptVersion(
        prompt_id=prompt_id,
        version=max_version + 1,
        content=body.content,
        content_hash=hash_val,
        labels=[],
        is_active=is_first,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@router.patch(
    "/{prompt_id}/versions/{version_id}/activate",
    response_model=PromptVersionOut,
)
def activate_version(
    prompt_id: UUID, version_id: UUID, db: Session = Depends(get_db)
):
    version = (
        db.query(PromptVersion)
        .filter(PromptVersion.id == version_id, PromptVersion.prompt_id == prompt_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    db.query(PromptVersion).filter(
        PromptVersion.prompt_id == prompt_id, PromptVersion.is_active == True
    ).update({"is_active": False})

    version.is_active = True
    db.commit()
    db.refresh(version)
    return version


@router.patch(
    "/{prompt_id}/versions/{version_id}/labels",
    response_model=PromptVersionOut,
)
def update_labels(
    prompt_id: UUID,
    version_id: UUID,
    body: LabelsUpdate,
    db: Session = Depends(get_db),
):
    version = (
        db.query(PromptVersion)
        .filter(PromptVersion.id == version_id, PromptVersion.prompt_id == prompt_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    version.labels = body.labels
    db.commit()
    db.refresh(version)
    return version


@router.post(
    "/{prompt_id}/rollback/{version_id}",
    response_model=PromptVersionOut,
)
def rollback_version(
    prompt_id: UUID, version_id: UUID, db: Session = Depends(get_db)
):
    version = (
        db.query(PromptVersion)
        .filter(PromptVersion.id == version_id, PromptVersion.prompt_id == prompt_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    db.query(PromptVersion).filter(
        PromptVersion.prompt_id == prompt_id, PromptVersion.is_active == True
    ).update({"is_active": False})

    version.is_active = True
    db.commit()
    db.refresh(version)
    return version


@router.get("/{prompt_id}/diff/{v1_id}/{v2_id}", response_model=DiffOut)
def diff_versions(
    prompt_id: UUID, v1_id: UUID, v2_id: UUID, db: Session = Depends(get_db)
):
    v1 = (
        db.query(PromptVersion)
        .filter(PromptVersion.id == v1_id, PromptVersion.prompt_id == prompt_id)
        .first()
    )
    v2 = (
        db.query(PromptVersion)
        .filter(PromptVersion.id == v2_id, PromptVersion.prompt_id == prompt_id)
        .first()
    )
    if not v1 or not v2:
        raise HTTPException(status_code=404, detail="Version not found")

    diff = "\n".join(
        difflib.unified_diff(
            v1.content.splitlines(),
            v2.content.splitlines(),
            fromfile=f"v{v1.version}",
            tofile=f"v{v2.version}",
            lineterm="",
        )
    )
    return DiffOut(
        v1_id=v1.id,
        v2_id=v2.id,
        v1_version=v1.version,
        v2_version=v2.version,
        diff=diff,
    )
