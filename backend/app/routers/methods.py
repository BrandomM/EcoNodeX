"""CRUD for collection methods catalog."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Method
from ..schemas import MethodCreate, MethodOut, MethodUpdate

router = APIRouter(prefix="/api/methods", tags=["methods"])


@router.get("", response_model=List[MethodOut])
def list_methods(project_id: int = Query(...), db: Session = Depends(get_db)):
    return db.query(Method).filter_by(project_id=project_id).order_by(Method.code).all()


@router.post("", response_model=MethodOut, status_code=201)
def create_method(body: MethodCreate, db: Session = Depends(get_db)):
    method = Method(**body.model_dump())
    db.add(method)
    db.commit()
    db.refresh(method)
    return method


@router.get("/{method_id}", response_model=MethodOut)
def get_method(method_id: int, db: Session = Depends(get_db)):
    method = db.get(Method, method_id)
    if not method:
        raise HTTPException(404, "Method not found")
    return method


@router.patch("/{method_id}", response_model=MethodOut)
def update_method(method_id: int, body: MethodUpdate, db: Session = Depends(get_db)):
    method = db.get(Method, method_id)
    if not method:
        raise HTTPException(404, "Method not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(method, k, v)
    db.commit()
    db.refresh(method)
    return method


@router.delete("/{method_id}", status_code=204)
def delete_method(method_id: int, db: Session = Depends(get_db)):
    method = db.get(Method, method_id)
    if not method:
        raise HTTPException(404, "Method not found")
    db.delete(method)
    db.commit()
