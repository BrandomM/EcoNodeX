"""CRUD for sampling events and replicates."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Replicate, SamplingEvent
from ..schemas import (
    ReplicateCreate, ReplicateOut, ReplicateUpdate,
    SamplingEventCreate, SamplingEventOut, SamplingEventUpdate,
)

router = APIRouter(prefix="/api/sampling", tags=["sampling"])


# ---------------------------------------------------------------------------
# Sampling events
# ---------------------------------------------------------------------------

@router.get("/events", response_model=List[SamplingEventOut])
def list_events(
    project_id: int = Query(...),
    location_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(SamplingEvent).filter_by(project_id=project_id)
    if location_id:
        q = q.filter_by(location_id=location_id)
    events = q.order_by(SamplingEvent.start_date.desc()).all()
    result = []
    for ev in events:
        out = SamplingEventOut.model_validate(ev)
        out.location_name = ev.location.name if ev.location else None
        out.replicate_count = len(ev.replicates)
        result.append(out)
    return result


@router.post("/events", response_model=SamplingEventOut, status_code=201)
def create_event(body: SamplingEventCreate, db: Session = Depends(get_db)):
    ev = SamplingEvent(**body.model_dump())
    db.add(ev)
    db.commit()
    db.refresh(ev)
    out = SamplingEventOut.model_validate(ev)
    out.location_name = ev.location.name if ev.location else None
    out.replicate_count = 0
    return out


@router.get("/events/{event_id}", response_model=SamplingEventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    ev = db.get(SamplingEvent, event_id)
    if not ev:
        raise HTTPException(404, "Event not found")
    out = SamplingEventOut.model_validate(ev)
    out.location_name = ev.location.name if ev.location else None
    out.replicate_count = len(ev.replicates)
    return out


@router.patch("/events/{event_id}", response_model=SamplingEventOut)
def update_event(event_id: int, body: SamplingEventUpdate, db: Session = Depends(get_db)):
    ev = db.get(SamplingEvent, event_id)
    if not ev:
        raise HTTPException(404, "Event not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(ev, k, v)
    db.commit()
    db.refresh(ev)
    out = SamplingEventOut.model_validate(ev)
    out.location_name = ev.location.name if ev.location else None
    out.replicate_count = len(ev.replicates)
    return out


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    ev = db.get(SamplingEvent, event_id)
    if not ev:
        raise HTTPException(404, "Event not found")
    db.delete(ev)
    db.commit()


# ---------------------------------------------------------------------------
# Replicates
# ---------------------------------------------------------------------------

@router.get("/events/{event_id}/replicates", response_model=List[ReplicateOut])
def list_replicates(event_id: int, db: Session = Depends(get_db)):
    reps = db.query(Replicate).filter_by(event_id=event_id).order_by(Replicate.code).all()
    result = []
    for r in reps:
        out = ReplicateOut.model_validate(r)
        out.method_label = r.method.label if r.method else None
        out.record_count = len(r.occurrence_records)
        result.append(out)
    return result


@router.post("/replicates", response_model=ReplicateOut, status_code=201)
def create_replicate(body: ReplicateCreate, db: Session = Depends(get_db)):
    rep = Replicate(**body.model_dump())
    db.add(rep)
    db.commit()
    db.refresh(rep)
    out = ReplicateOut.model_validate(rep)
    out.method_label = rep.method.label if rep.method else None
    out.record_count = 0
    return out


@router.get("/replicates/{replicate_id}", response_model=ReplicateOut)
def get_replicate(replicate_id: int, db: Session = Depends(get_db)):
    rep = db.get(Replicate, replicate_id)
    if not rep:
        raise HTTPException(404, "Replicate not found")
    out = ReplicateOut.model_validate(rep)
    out.method_label = rep.method.label if rep.method else None
    out.record_count = len(rep.occurrence_records)
    return out


@router.patch("/replicates/{replicate_id}", response_model=ReplicateOut)
def update_replicate(replicate_id: int, body: ReplicateUpdate, db: Session = Depends(get_db)):
    rep = db.get(Replicate, replicate_id)
    if not rep:
        raise HTTPException(404, "Replicate not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(rep, k, v)
    db.commit()
    db.refresh(rep)
    out = ReplicateOut.model_validate(rep)
    out.method_label = rep.method.label if rep.method else None
    out.record_count = len(rep.occurrence_records)
    return out


@router.delete("/replicates/{replicate_id}", status_code=204)
def delete_replicate(replicate_id: int, db: Session = Depends(get_db)):
    rep = db.get(Replicate, replicate_id)
    if not rep:
        raise HTTPException(404, "Replicate not found")
    db.delete(rep)
    db.commit()
