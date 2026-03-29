"""Analysis endpoints: Shannon, Simpson, accumulation, beta diversity."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import OccurrenceRecord, Replicate, SamplingEvent, Taxon
from ..schemas import AnalysisRequest, AnalysisResult, AnalysisScope
from ..services import analyses_service as svc

router = APIRouter(prefix="/api/analyses", tags=["analyses"])


def _get_replicates(scope: AnalysisScope, project_id: int, db: Session) -> List[Replicate]:
    """Return replicates matching the given scope."""
    q = (
        db.query(Replicate)
        .join(SamplingEvent)
        .filter(SamplingEvent.project_id == project_id)
    )
    if scope.type == "replicate" and scope.id:
        q = q.filter(Replicate.id == scope.id)
    elif scope.type == "event" and scope.id:
        q = q.filter(Replicate.event_id == scope.id)
    elif scope.type == "location" and scope.id:
        # Include subtree
        all_locs = _location_subtree(scope.id, project_id, db)
        q = q.filter(SamplingEvent.location_id.in_(all_locs))
    # else: project-level — all replicates
    return q.all()


def _location_subtree(location_id: int, project_id: int, db: Session):
    from ..models import Location
    all_locs = db.query(Location).filter_by(project_id=project_id).all()
    result = set()

    def collect(lid):
        result.add(lid)
        for l in all_locs:
            if l.parent_location_id == lid:
                collect(l.id)

    collect(location_id)
    return list(result)


def _build_samples(replicates: List[Replicate]):
    """Return (samples_list, labels_list) where samples_list[i] = {taxon_id: count}."""
    samples = []
    labels = []
    for rep in replicates:
        d = svc.records_to_sample_dict(rep.occurrence_records)
        samples.append(d)
        labels.append(f"{rep.code} (E{rep.event_id})")
    return samples, labels


def _all_counts(samples: List[dict]) -> List[int]:
    """Merge all samples into one count vector."""
    merged: dict = {}
    for s in samples:
        for tid, c in s.items():
            merged[tid] = merged.get(tid, 0) + c
    return list(merged.values())


@router.post("/shannon", response_model=AnalysisResult)
def run_shannon(body: AnalysisRequest, db: Session = Depends(get_db)):
    reps = _get_replicates(body.scope, body.project_id, db)
    samples, labels = _build_samples(reps)
    counts = _all_counts(samples)

    results = {
        "H": svc.shannon_wiener(counts),
        "S": svc.richness(counts),
        "N": svc.abundance(counts),
        "J": svc.pielou_evenness(counts),
        "per_replicate": [],
    }
    for s, label in zip(samples, labels):
        c = svc.sample_dict_to_counts(s)
        results["per_replicate"].append({
            "label": label,
            "H": svc.shannon_wiener(c),
            "S": svc.richness(c),
            "N": svc.abundance(c),
        })

    return AnalysisResult(
        analysis_type="shannon",
        scope=body.scope,
        timestamp=datetime.utcnow().isoformat(),
        parameters={},
        results=results,
    )


@router.post("/simpson", response_model=AnalysisResult)
def run_simpson(body: AnalysisRequest, db: Session = Depends(get_db)):
    reps = _get_replicates(body.scope, body.project_id, db)
    samples, labels = _build_samples(reps)
    counts = _all_counts(samples)

    results = {
        "D": svc.simpson_index(counts),
        "lambda": svc.simpson_dominance(counts),
        "S": svc.richness(counts),
        "N": svc.abundance(counts),
        "per_replicate": [],
    }
    for s, label in zip(samples, labels):
        c = svc.sample_dict_to_counts(s)
        results["per_replicate"].append({
            "label": label,
            "D": svc.simpson_index(c),
            "S": svc.richness(c),
            "N": svc.abundance(c),
        })

    return AnalysisResult(
        analysis_type="simpson",
        scope=body.scope,
        timestamp=datetime.utcnow().isoformat(),
        parameters={},
        results=results,
    )


@router.post("/accumulation", response_model=AnalysisResult)
def run_accumulation(body: AnalysisRequest, db: Session = Depends(get_db)):
    reps = _get_replicates(body.scope, body.project_id, db)
    samples, labels = _build_samples(reps)

    acc_result = svc.species_accumulation(samples, labels, n_permutations=body.permutations)
    plot_b64 = None
    try:
        plot_b64 = svc.plot_accumulation_b64(acc_result)
    except Exception:
        pass

    return AnalysisResult(
        analysis_type="accumulation",
        scope=body.scope,
        timestamp=datetime.utcnow().isoformat(),
        parameters={"permutations": body.permutations},
        results=acc_result,
        plot_b64=plot_b64,
    )


@router.post("/bray-curtis", response_model=AnalysisResult)
def run_bray_curtis(body: AnalysisRequest, db: Session = Depends(get_db)):
    reps = _get_replicates(body.scope, body.project_id, db)
    samples, labels = _build_samples(reps)

    if len(samples) < 2:
        raise HTTPException(400, "Se necesitan al menos 2 réplicas para beta-diversidad")

    matrix = svc.bray_curtis_matrix(samples)
    mean_d = svc.mean_dissimilarity(matrix)
    plot_b64 = None
    try:
        plot_b64 = svc.plot_beta_heatmap_b64(matrix, labels, "Bray-Curtis Disimilitud")
    except Exception:
        pass

    return AnalysisResult(
        analysis_type="bray_curtis",
        scope=body.scope,
        timestamp=datetime.utcnow().isoformat(),
        parameters={},
        results={"samples": labels, "matrix": matrix, "mean_dissimilarity": mean_d},
        plot_b64=plot_b64,
    )


@router.post("/jaccard", response_model=AnalysisResult)
def run_jaccard(body: AnalysisRequest, db: Session = Depends(get_db)):
    reps = _get_replicates(body.scope, body.project_id, db)
    samples, labels = _build_samples(reps)

    if len(samples) < 2:
        raise HTTPException(400, "Se necesitan al menos 2 réplicas para beta-diversidad")

    matrix = svc.jaccard_matrix(samples)
    mean_d = svc.mean_dissimilarity(matrix)
    plot_b64 = None
    try:
        plot_b64 = svc.plot_beta_heatmap_b64(matrix, labels, "Jaccard Disimilitud")
    except Exception:
        pass

    return AnalysisResult(
        analysis_type="jaccard",
        scope=body.scope,
        timestamp=datetime.utcnow().isoformat(),
        parameters={},
        results={"samples": labels, "matrix": matrix, "mean_dissimilarity": mean_d},
        plot_b64=plot_b64,
    )


@router.post("/richness", response_model=AnalysisResult)
def run_richness(body: AnalysisRequest, db: Session = Depends(get_db)):
    reps = _get_replicates(body.scope, body.project_id, db)
    samples, labels = _build_samples(reps)
    counts = _all_counts(samples)

    per_rep = []
    for s, label in zip(samples, labels):
        c = svc.sample_dict_to_counts(s)
        per_rep.append({
            "label": label,
            "S": svc.richness(c),
            "N": svc.abundance(c),
        })

    return AnalysisResult(
        analysis_type="richness",
        scope=body.scope,
        timestamp=datetime.utcnow().isoformat(),
        parameters={},
        results={
            "S_total": svc.richness(counts),
            "N_total": svc.abundance(counts),
            "per_replicate": per_rep,
        },
    )
