"""CRUD and merge for taxa (hierarchical, including morphospecies)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Media, MergeLog, OccurrenceRecord, Taxon
from ..schemas import (
    MergeExecute, MergeLogOut, MergePreview, MergePreviewOut,
    TaxonCreate, TaxonOut, TaxonUpdate,
)
from ..services.backup_service import create_backup

router = APIRouter(prefix="/api/taxa", tags=["taxa"])

MORPHOSPECIES_RANKS = {"morphospecies", "morpho-species", "morfoespecie"}


def _auto_alias(db: Session, project_id: int, scientific_name: str, rank: str) -> str:
    """Generate auto alias like 'Papilionidae 1', or 'Morfo 1' for morphospecies."""
    if rank.lower() in MORPHOSPECIES_RANKS:
        prefix = "Morfo"
    else:
        # Use first token of scientificName (family/genus)
        prefix = scientific_name.split()[0] if scientific_name else "Taxa"
    # Count existing taxa with same prefix to generate number
    existing = (
        db.query(Taxon)
        .filter(Taxon.project_id == project_id, Taxon.alias.like(f"{prefix} %"))
        .count()
    )
    return f"{prefix} {existing + 1}"


def _build_tree(taxa: List[Taxon], parent_id: Optional[int] = None) -> List[dict]:
    result = []
    for t in taxa:
        if t.parent_taxon_id == parent_id:
            children = _build_tree(taxa, t.id)
            d = TaxonOut.model_validate(t).model_dump()
            d["children"] = children
            result.append(d)
    return result


@router.get("", response_model=List[TaxonOut])
def list_taxa(
    project_id: int = Query(...),
    tree: bool = Query(False),
    search: Optional[str] = Query(None),
    rank: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Taxon).filter_by(project_id=project_id)
    if search:
        s = f"%{search}%"
        q = q.filter(
            Taxon.scientific_name.ilike(s)
            | Taxon.alias.ilike(s)
            | Taxon.common_name.ilike(s)
        )
    if rank:
        q = q.filter(Taxon.rank.ilike(rank))
    taxa = q.order_by(Taxon.scientific_name).all()
    if tree and not search and not rank:
        return _build_tree(taxa)
    return taxa


@router.post("", response_model=TaxonOut, status_code=201)
def create_taxon(body: TaxonCreate, db: Session = Depends(get_db)):
    data = body.model_dump()
    if not data.get("alias"):
        data["alias"] = _auto_alias(db, data["project_id"], data["scientific_name"], data["rank"])
    taxon = Taxon(**data)
    db.add(taxon)
    db.commit()
    db.refresh(taxon)
    return taxon


@router.get("/{taxon_id}", response_model=TaxonOut)
def get_taxon(taxon_id: int, db: Session = Depends(get_db)):
    taxon = db.get(Taxon, taxon_id)
    if not taxon:
        raise HTTPException(404, "Taxon not found")
    return taxon


@router.patch("/{taxon_id}", response_model=TaxonOut)
def update_taxon(taxon_id: int, body: TaxonUpdate, db: Session = Depends(get_db)):
    taxon = db.get(Taxon, taxon_id)
    if not taxon:
        raise HTTPException(404, "Taxon not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(taxon, k, v)
    db.commit()
    db.refresh(taxon)
    return taxon


@router.delete("/{taxon_id}", status_code=204)
def delete_taxon(taxon_id: int, db: Session = Depends(get_db)):
    taxon = db.get(Taxon, taxon_id)
    if not taxon:
        raise HTTPException(404, "Taxon not found")
    # Check for dependent records
    recs = db.query(OccurrenceRecord).filter_by(taxon_id=taxon_id).count()
    if recs > 0:
        raise HTTPException(409, f"Taxon has {recs} occurrence records. Merge or reassign first.")
    db.delete(taxon)
    db.commit()


@router.get("/{taxon_id}/subtree-ids")
def taxon_subtree_ids(taxon_id: int, db: Session = Depends(get_db)):
    taxon = db.get(Taxon, taxon_id)
    if not taxon:
        raise HTTPException(404, "Taxon not found")
    all_taxa = db.query(Taxon).filter_by(project_id=taxon.project_id).all()
    result = set()

    def collect(tid):
        result.add(tid)
        for t in all_taxa:
            if t.parent_taxon_id == tid:
                collect(t.id)

    collect(taxon_id)
    return {"ids": list(result)}


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

@router.post("/merge/preview", response_model=MergePreviewOut)
def merge_preview(body: MergePreview, db: Session = Depends(get_db)):
    src = db.get(Taxon, body.source_taxon_id)
    tgt = db.get(Taxon, body.target_taxon_id)
    if not src:
        raise HTTPException(404, "Source taxon not found")
    if not tgt:
        raise HTTPException(404, "Target taxon not found")
    if src.id == tgt.id:
        raise HTTPException(400, "Source and target must differ")

    records_affected = db.query(OccurrenceRecord).filter_by(taxon_id=src.id).count()
    media_affected = (
        db.query(Media)
        .filter_by(linked_to_type="taxon", linked_to_id=src.id)
        .count()
    )
    return MergePreviewOut(
        source_taxon_id=src.id,
        source_taxon_name=src.scientific_name,
        source_taxon_alias=src.alias,
        target_taxon_id=tgt.id,
        target_taxon_name=tgt.scientific_name,
        records_affected=records_affected,
        media_affected=media_affected,
    )


@router.post("/merge/execute", response_model=MergeLogOut)
def merge_execute(body: MergeExecute, db: Session = Depends(get_db)):
    if body.confirmation != "CONFIRMAR":
        raise HTTPException(400, "Confirmation text must be exactly 'CONFIRMAR'")

    src = db.get(Taxon, body.source_taxon_id)
    tgt = db.get(Taxon, body.target_taxon_id)
    if not src or not tgt:
        raise HTTPException(404, "Source or target taxon not found")
    if src.id == tgt.id:
        raise HTTPException(400, "Source and target must differ")
    if src.project_id != tgt.project_id:
        raise HTTPException(400, "Taxa must belong to the same project")

    # Create backup BEFORE any changes
    backup_path = create_backup(src.project_id, label="pre_merge")

    # Count affected
    records_affected = db.query(OccurrenceRecord).filter_by(taxon_id=src.id).count()
    media_affected = (
        db.query(Media)
        .filter_by(linked_to_type="taxon", linked_to_id=src.id)
        .count()
    )

    # Remap occurrence records
    db.query(OccurrenceRecord).filter_by(taxon_id=src.id).update(
        {"taxon_id": tgt.id}, synchronize_session="fetch"
    )

    # Remap media
    db.query(Media).filter_by(linked_to_type="taxon", linked_to_id=src.id).update(
        {"linked_to_id": tgt.id}, synchronize_session="fetch"
    )

    # Reparent children of source to target
    db.query(Taxon).filter_by(parent_taxon_id=src.id).update(
        {"parent_taxon_id": tgt.id}, synchronize_session="fetch"
    )

    # Log the merge
    log = MergeLog(
        project_id=src.project_id,
        source_taxon_id=src.id,
        source_taxon_name=src.scientific_name,
        source_taxon_alias=src.alias,
        target_taxon_id=tgt.id,
        target_taxon_name=tgt.scientific_name,
        records_affected=records_affected,
        media_affected=media_affected,
        backup_path=str(backup_path),
    )
    db.add(log)

    # Delete source
    db.delete(src)
    db.commit()
    db.refresh(log)
    return log


@router.get("/merge/logs", response_model=List[MergeLogOut])
def list_merge_logs(project_id: int = Query(...), db: Session = Depends(get_db)):
    return (
        db.query(MergeLog)
        .filter_by(project_id=project_id)
        .order_by(MergeLog.created_at.desc())
        .all()
    )
