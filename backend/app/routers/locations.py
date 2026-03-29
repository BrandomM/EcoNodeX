"""CRUD for locations (hierarchical)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Location
from ..schemas import LocationCreate, LocationOut, LocationUpdate

router = APIRouter(prefix="/api/locations", tags=["locations"])


def _build_tree(locs: List[Location], parent_id: Optional[int] = None) -> List[dict]:
    """Recursively build a tree of LocationOut dicts."""
    result = []
    for loc in locs:
        if loc.parent_location_id == parent_id:
            children = _build_tree(locs, loc.id)
            d = LocationOut.model_validate(loc).model_dump()
            d["children"] = children
            result.append(d)
    return result


@router.get("", response_model=List[LocationOut])
def list_locations(
    project_id: int = Query(...),
    tree: bool = Query(False),
    db: Session = Depends(get_db),
):
    locs = db.query(Location).filter_by(project_id=project_id).order_by(Location.name).all()
    if tree:
        return _build_tree(locs)
    return locs


@router.post("", response_model=LocationOut, status_code=201)
def create_location(body: LocationCreate, db: Session = Depends(get_db)):
    loc = Location(**body.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@router.get("/{location_id}", response_model=LocationOut)
def get_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(404, "Location not found")
    return loc


@router.patch("/{location_id}", response_model=LocationOut)
def update_location(location_id: int, body: LocationUpdate, db: Session = Depends(get_db)):
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(404, "Location not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(loc, k, v)
    db.commit()
    db.refresh(loc)
    return loc


@router.delete("/{location_id}", status_code=204)
def delete_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(404, "Location not found")
    db.delete(loc)
    db.commit()


@router.get("/{location_id}/subtree-ids")
def subtree_ids(location_id: int, db: Session = Depends(get_db)):
    """Return all location IDs in the subtree rooted at location_id (inclusive)."""
    all_locs = db.query(Location).filter_by(project_id=db.get(Location, location_id).project_id).all()
    result = set()

    def collect(lid):
        result.add(lid)
        for loc in all_locs:
            if loc.parent_location_id == lid:
                collect(loc.id)

    collect(location_id)
    return {"ids": list(result)}
