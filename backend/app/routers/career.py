from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import CareerProfile
from app.schemas import CareerProfileIn, CareerProfileOut

router = APIRouter(tags=["career"])


@router.get("/career", response_model=CareerProfileOut)
def get_career(db: Session = Depends(get_db)):
    profile = db.scalar(
        select(CareerProfile).where(CareerProfile.user_id == settings.default_user_id)
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="career profile not registered")
    return profile


@router.put("/career", response_model=CareerProfileOut)
def upsert_career(body: CareerProfileIn, db: Session = Depends(get_db)):
    profile = db.scalar(
        select(CareerProfile).where(CareerProfile.user_id == settings.default_user_id)
    )
    if profile is None:
        profile = CareerProfile(user_id=settings.default_user_id, **body.model_dump())
        db.add(profile)
    else:
        for field, value in body.model_dump().items():
            setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
