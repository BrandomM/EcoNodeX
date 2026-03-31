"""CRUD for occurrence records."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import OccurrenceRecord, Replicate, SamplingEvent, Taxon
from ..schemas import OccurrenceRecordCreate, OccurrenceRecordOut, OccurrenceRecordUpdate

router = APIRouter(prefix="/api/records", tags=["records"])


def _enrich(r: OccurrenceRecord) -> OccurrenceRecordOut:
    out = OccurrenceRecordOut.model_validate(r)
    if r.taxon:
        out.taxon_name = r.taxon.scientific_name
        out.taxon_alias = r.taxon.alias
        if r.taxon.media:
            out.taxon_profile_media_id = r.taxon.media[0].id
    if r.method:
        out.method_label = r.method.label
    return out


@router.get("", response_model=List[OccurrenceRecordOut])
def list_records(
    project_id: int = Query(...),
    replicate_id: Optional[int] = Query(None),
    taxon_id: Optional[int] = Query(None),
    location_id: Optional[int] = Query(None),
    event_id: Optional[int] = Query(None),
    method_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db),
):
    q = (
        db.query(OccurrenceRecord)
        .join(Replicate)
        .join(SamplingEvent)
        .filter(SamplingEvent.project_id == project_id)
    )
    if replicate_id:
        q = q.filter(OccurrenceRecord.replicate_id == replicate_id)
    if taxon_id:
        q = q.filter(OccurrenceRecord.taxon_id == taxon_id)
    if event_id:
        q = q.filter(Replicate.event_id == event_id)
    if location_id:
        q = q.filter(SamplingEvent.location_id == location_id)
    if method_id:
        q = q.filter(OccurrenceRecord.method_id == method_id)
    if date_from:
        q = q.filter(SamplingEvent.start_date >= date_from)
    if date_to:
        q = q.filter(SamplingEvent.start_date <= date_to)

    recs = q.order_by(OccurrenceRecord.id.desc()).offset(skip).limit(limit).all()
    return [_enrich(r) for r in recs]


@router.post("", response_model=OccurrenceRecordOut, status_code=201)
def create_record(body: OccurrenceRecordCreate, db: Session = Depends(get_db)):
    rec = OccurrenceRecord(**body.model_dump())
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return _enrich(rec)


@router.get("/{record_id}", response_model=OccurrenceRecordOut)
def get_record(record_id: int, db: Session = Depends(get_db)):
    rec = db.get(OccurrenceRecord, record_id)
    if not rec:
        raise HTTPException(404, "Record not found")
    return _enrich(rec)


@router.patch("/{record_id}", response_model=OccurrenceRecordOut)
def update_record(record_id: int, body: OccurrenceRecordUpdate, db: Session = Depends(get_db)):
    rec = db.get(OccurrenceRecord, record_id)
    if not rec:
        raise HTTPException(404, "Record not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(rec, k, v)
    db.commit()
    db.refresh(rec)
    return _enrich(rec)


@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: int, db: Session = Depends(get_db)):
    rec = db.get(OccurrenceRecord, record_id)
    if not rec:
        raise HTTPException(404, "Record not found")
    db.delete(rec)
    db.commit()
