"""
Export service: CSV/Excel, Darwin Core Archive (DwC-A), project ZIP.
"""
from __future__ import annotations

import csv
import io
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models import (
    Location, Media, Method, MergeLog, OccurrenceRecord,
    Project, Replicate, SamplingEvent, Taxon,
)


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def _write_csv(rows: List[Dict], fieldnames: List[str]) -> bytes:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")   # BOM for Excel compat


# ---------------------------------------------------------------------------
# Entity serialisers (flat dicts for CSV/Excel rows)
# ---------------------------------------------------------------------------

def _taxa_rows(project_id: int, db: Session) -> List[Dict]:
    taxa = db.query(Taxon).filter_by(project_id=project_id).all()
    return [
        {
            "id": t.id,
            "parent_taxon_id": t.parent_taxon_id,
            "scientific_name": t.scientific_name,
            "rank": t.rank,
            "common_name": t.common_name,
            "alias": t.alias,
            "description": t.description,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
        }
        for t in taxa
    ]


def _locations_rows(project_id: int, db: Session) -> List[Dict]:
    locs = db.query(Location).filter_by(project_id=project_id).all()
    return [
        {
            "id": l.id,
            "parent_location_id": l.parent_location_id,
            "name": l.name,
            "type": l.type,
            "latitude": l.latitude,
            "longitude": l.longitude,
            "altitude": l.altitude,
            "description": l.description,
            "created_at": l.created_at,
            "updated_at": l.updated_at,
        }
        for l in locs
    ]


def _events_rows(project_id: int, db: Session) -> List[Dict]:
    evts = db.query(SamplingEvent).filter_by(project_id=project_id).all()
    return [
        {
            "id": e.id,
            "location_id": e.location_id,
            "start_date": e.start_date,
            "end_date": e.end_date,
            "description": e.description,
            "created_at": e.created_at,
            "updated_at": e.updated_at,
        }
        for e in evts
    ]


def _replicates_rows(project_id: int, db: Session) -> List[Dict]:
    reps = (
        db.query(Replicate)
        .join(SamplingEvent)
        .filter(SamplingEvent.project_id == project_id)
        .all()
    )
    return [
        {
            "id": r.id,
            "event_id": r.event_id,
            "code": r.code,
            "method_id": r.method_id,
            "notes": r.notes,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        for r in reps
    ]


def _records_rows(project_id: int, db: Session) -> List[Dict]:
    recs = (
        db.query(OccurrenceRecord)
        .join(Replicate)
        .join(SamplingEvent)
        .filter(SamplingEvent.project_id == project_id)
        .all()
    )
    return [
        {
            "id": r.id,
            "replicate_id": r.replicate_id,
            "taxon_id": r.taxon_id,
            "taxon_scientific_name": r.taxon.scientific_name if r.taxon else "",
            "taxon_alias": r.taxon.alias if r.taxon else "",
            "individual_count": r.individual_count,
            "method_id": r.method_id,
            "date_time": r.date_time,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "notes": r.notes,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        for r in recs
    ]


def _methods_rows(project_id: int, db: Session) -> List[Dict]:
    methods = db.query(Method).filter_by(project_id=project_id).all()
    return [
        {
            "id": m.id,
            "code": m.code,
            "label": m.label,
            "description": m.description,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        }
        for m in methods
    ]


def _media_rows(project_id: int, db: Session) -> List[Dict]:
    media = db.query(Media).filter_by(project_id=project_id).all()
    return [
        {
            "id": m.id,
            "file_name": m.file_name,
            "relative_path": m.relative_path,
            "size_bytes": m.size_bytes,
            "mime_type": m.mime_type,
            "linked_to_type": m.linked_to_type,
            "linked_to_id": m.linked_to_id,
            "is_profile": m.is_profile,
            "created_at": m.created_at,
        }
        for m in media
    ]


# ---------------------------------------------------------------------------
# Abundance / presence-absence matrices
# ---------------------------------------------------------------------------

def _abundance_matrix(project_id: int, db: Session) -> bytes:
    """Replicates × Taxa matrix of total individual_count."""
    reps = (
        db.query(Replicate).join(SamplingEvent)
        .filter(SamplingEvent.project_id == project_id)
        .all()
    )
    taxa = db.query(Taxon).filter_by(project_id=project_id).all()
    taxon_ids = [t.id for t in taxa]
    taxon_labels = {t.id: (t.alias or t.scientific_name) for t in taxa}

    buf = io.StringIO()
    w = csv.writer(buf)
    header = ["replicate_id", "event_id", "replicate_code"] + [taxon_labels[tid] for tid in taxon_ids]
    w.writerow(header)

    for rep in reps:
        counts = {r.taxon_id: r.individual_count for r in rep.occurrence_records}
        row = [rep.id, rep.event_id, rep.code] + [counts.get(tid, 0) for tid in taxon_ids]
        w.writerow(row)
    return buf.getvalue().encode("utf-8-sig")


def _presence_absence_matrix(project_id: int, db: Session) -> bytes:
    reps = (
        db.query(Replicate).join(SamplingEvent)
        .filter(SamplingEvent.project_id == project_id)
        .all()
    )
    taxa = db.query(Taxon).filter_by(project_id=project_id).all()
    taxon_ids = [t.id for t in taxa]
    taxon_labels = {t.id: (t.alias or t.scientific_name) for t in taxa}

    buf = io.StringIO()
    w = csv.writer(buf)
    header = ["replicate_id", "event_id", "replicate_code"] + [taxon_labels[tid] for tid in taxon_ids]
    w.writerow(header)

    for rep in reps:
        present = {r.taxon_id for r in rep.occurrence_records if r.individual_count > 0}
        row = [rep.id, rep.event_id, rep.code] + [1 if tid in present else 0 for tid in taxon_ids]
        w.writerow(row)
    return buf.getvalue().encode("utf-8-sig")


# ---------------------------------------------------------------------------
# Excel export (all sheets in one workbook)
# ---------------------------------------------------------------------------

def export_excel(project_id: int, db: Session) -> bytes:
    try:
        import openpyxl
    except ImportError:
        raise RuntimeError("openpyxl not installed")

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    sheets = {
        "Taxa": (_taxa_rows(project_id, db), ["id","parent_taxon_id","scientific_name","rank","common_name","alias","description","created_at","updated_at"]),
        "Locations": (_locations_rows(project_id, db), ["id","parent_location_id","name","type","latitude","longitude","altitude","description","created_at","updated_at"]),
        "Events": (_events_rows(project_id, db), ["id","location_id","start_date","end_date","description","created_at","updated_at"]),
        "Replicates": (_replicates_rows(project_id, db), ["id","event_id","code","method_id","notes","created_at","updated_at"]),
        "Records": (_records_rows(project_id, db), ["id","replicate_id","taxon_id","taxon_scientific_name","taxon_alias","individual_count","method_id","date_time","latitude","longitude","notes","created_at","updated_at"]),
        "Methods": (_methods_rows(project_id, db), ["id","code","label","description","created_at","updated_at"]),
        "Media": (_media_rows(project_id, db), ["id","file_name","relative_path","size_bytes","mime_type","linked_to_type","linked_to_id","is_profile","created_at"]),
    }

    for sheet_name, (rows, fields) in sheets.items():
        ws = wb.create_sheet(title=sheet_name)
        ws.append(fields)
        for row in rows:
            ws.append([row.get(f, "") for f in fields])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Darwin Core Archive (DwC-A)
# ---------------------------------------------------------------------------

META_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<archive xmlns="http://rs.tdwg.org/dwc/text/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://rs.tdwg.org/dwc/text/
           http://rs.tdwg.org/dwc/text/tdwg_dwc_text.xsd">

  <!-- EVENT CORE -->
  <core encoding="UTF-8" fieldsTerminatedBy="," linesTerminatedBy="\\n"
        fieldsEnclosedBy='"' ignoreHeaderLines="1"
        rowType="http://rs.tdwg.org/dwc/terms/Event">
    <files><location>event.csv</location></files>
    <id index="0"/>
    <field index="1"  term="http://rs.tdwg.org/dwc/terms/parentEventID"/>
    <field index="2"  term="http://rs.tdwg.org/dwc/terms/eventDate"/>
    <field index="3"  term="http://rs.tdwg.org/dwc/terms/samplingProtocol"/>
    <field index="4"  term="http://rs.tdwg.org/dwc/terms/locationID"/>
    <field index="5"  term="http://rs.tdwg.org/dwc/terms/locality"/>
    <field index="6"  term="http://rs.tdwg.org/dwc/terms/decimalLatitude"/>
    <field index="7"  term="http://rs.tdwg.org/dwc/terms/decimalLongitude"/>
  </core>

  <!-- OCCURRENCE EXTENSION -->
  <extension encoding="UTF-8" fieldsTerminatedBy="," linesTerminatedBy="\\n"
             fieldsEnclosedBy='"' ignoreHeaderLines="1"
             rowType="http://rs.tdwg.org/dwc/terms/Occurrence">
    <files><location>occurrence.csv</location></files>
    <coreid index="0"/>
    <field index="1"  term="http://rs.tdwg.org/dwc/terms/occurrenceID"/>
    <field index="2"  term="http://rs.tdwg.org/dwc/terms/basisOfRecord"/>
    <field index="3"  term="http://rs.tdwg.org/dwc/terms/scientificName"/>
    <field index="4"  term="http://rs.tdwg.org/dwc/terms/taxonRank"/>
    <field index="5"  term="http://rs.tdwg.org/dwc/terms/individualCount"/>
    <field index="6"  term="http://rs.tdwg.org/dwc/terms/occurrenceStatus"/>
    <field index="7"  term="http://rs.tdwg.org/dwc/terms/vernacularName"/>
    <field index="8"  term="http://rs.tdwg.org/dwc/terms/taxonID"/>
    <field index="9"  term="http://rs.tdwg.org/dwc/terms/geodeticDatum"/>
  </extension>

  <!-- TAXON EXTENSION -->
  <extension encoding="UTF-8" fieldsTerminatedBy="," linesTerminatedBy="\\n"
             fieldsEnclosedBy='"' ignoreHeaderLines="1"
             rowType="http://rs.tdwg.org/dwc/terms/Taxon">
    <files><location>taxon.csv</location></files>
    <coreid index="0"/>
    <field index="1"  term="http://rs.tdwg.org/dwc/terms/taxonID"/>
    <field index="2"  term="http://rs.tdwg.org/dwc/terms/scientificName"/>
    <field index="3"  term="http://rs.tdwg.org/dwc/terms/taxonRank"/>
    <field index="4"  term="http://rs.tdwg.org/dwc/terms/vernacularName"/>
    <field index="5"  term="http://rs.tdwg.org/dwc/terms/parentNameUsageID"/>
  </extension>

  <!-- MULTIMEDIA EXTENSION -->
  <extension encoding="UTF-8" fieldsTerminatedBy="," linesTerminatedBy="\\n"
             fieldsEnclosedBy='"' ignoreHeaderLines="1"
             rowType="http://rs.gbif.org/terms/1.0/Multimedia">
    <files><location>multimedia.csv</location></files>
    <coreid index="0"/>
    <field index="1"  term="http://purl.org/dc/terms/identifier"/>
    <field index="2"  term="http://purl.org/dc/terms/type"/>
    <field index="3"  term="http://purl.org/dc/terms/format"/>
    <field index="4"  term="http://purl.org/dc/terms/references"/>
  </extension>

</archive>
"""


def _event_rows_dwca(project_id: int, db: Session) -> List[Dict]:
    """
    Rows for event.csv.
    Convention: eventID = "E{event.id}" for sampling events,
                           "R{replicate.id}" for replicates (parentEventID = "E{event.id}").
    """
    rows = []
    events = db.query(SamplingEvent).filter_by(project_id=project_id).all()
    for ev in events:
        rows.append({
            "eventID": f"E{ev.id}",
            "parentEventID": "",
            "eventDate": f"{ev.start_date}/{ev.end_date}" if ev.end_date else ev.start_date,
            "samplingProtocol": "",
            "locationID": f"L{ev.location_id}",
            "locality": ev.location.name if ev.location else "",
            "decimalLatitude": ev.location.latitude if ev.location else "",
            "decimalLongitude": ev.location.longitude if ev.location else "",
        })
        for rep in ev.replicates:
            method_label = rep.method.label if rep.method else ""
            rows.append({
                "eventID": f"R{rep.id}",
                "parentEventID": f"E{ev.id}",
                "eventDate": ev.start_date,
                "samplingProtocol": method_label,
                "locationID": f"L{ev.location_id}",
                "locality": ev.location.name if ev.location else "",
                "decimalLatitude": ev.location.latitude if ev.location else "",
                "decimalLongitude": ev.location.longitude if ev.location else "",
            })
    return rows


def _occurrence_rows_dwca(project_id: int, db: Session) -> List[Dict]:
    rows = []
    recs = (
        db.query(OccurrenceRecord)
        .join(Replicate)
        .join(SamplingEvent)
        .filter(SamplingEvent.project_id == project_id)
        .all()
    )
    for r in recs:
        t = r.taxon
        rows.append({
            "eventID": f"R{r.replicate_id}",
            "occurrenceID": f"OCC{r.id}",
            "basisOfRecord": "HumanObservation",
            "scientificName": t.scientific_name if t else "",
            "taxonRank": t.rank if t else "",
            "individualCount": r.individual_count,
            "occurrenceStatus": "present" if r.individual_count > 0 else "absent",
            "vernacularName": t.common_name if t else "",
            "taxonID": f"T{r.taxon_id}",
            "geodeticDatum": "WGS84",
        })
    return rows


def _taxon_rows_dwca(project_id: int, db: Session) -> List[Dict]:
    taxa = db.query(Taxon).filter_by(project_id=project_id).all()
    # We need a "coreid" — we'll use a dummy eventID placeholder; DwC taxon extension
    # can be linked to records via taxonID. We'll use taxon.id as coreid.
    return [
        {
            "coreid": f"T{t.id}",
            "taxonID": f"T{t.id}",
            "scientificName": t.scientific_name,
            "taxonRank": t.rank,
            "vernacularName": t.common_name or "",
            "parentNameUsageID": f"T{t.parent_taxon_id}" if t.parent_taxon_id else "",
        }
        for t in taxa
    ]


def _multimedia_rows_dwca(project_id: int, db: Session) -> List[Dict]:
    media = db.query(Media).filter_by(project_id=project_id).all()
    rows = []
    for m in media:
        # Determine coreid: map to the event/record where possible
        if m.linked_to_type == "record":
            coreid = f"OCC{m.linked_to_id}"
        elif m.linked_to_type == "taxon":
            coreid = f"T{m.linked_to_id}"
        elif m.linked_to_type == "location":
            coreid = f"L{m.linked_to_id}"
        else:
            coreid = ""
        rows.append({
            "coreid": coreid,
            "identifier": m.relative_path,
            "type": "StillImage" if (m.mime_type or "").startswith("image/") else "",
            "format": m.mime_type or "",
            "references": "",
        })
    return rows


def export_dwca(project_id: int, db: Session) -> bytes:
    """Return bytes of a DwC-A ZIP archive."""
    event_rows = _event_rows_dwca(project_id, db)
    occ_rows = _occurrence_rows_dwca(project_id, db)
    taxon_rows = _taxon_rows_dwca(project_id, db)
    mm_rows = _multimedia_rows_dwca(project_id, db)

    def to_csv(rows: List[Dict], fields: List[str]) -> bytes:
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
        return buf.getvalue().encode("utf-8")

    event_csv = to_csv(event_rows, ["eventID","parentEventID","eventDate","samplingProtocol","locationID","locality","decimalLatitude","decimalLongitude"])
    occ_csv = to_csv(occ_rows, ["eventID","occurrenceID","basisOfRecord","scientificName","taxonRank","individualCount","occurrenceStatus","vernacularName","taxonID","geodeticDatum"])
    taxon_csv = to_csv(taxon_rows, ["coreid","taxonID","scientificName","taxonRank","vernacularName","parentNameUsageID"])
    mm_csv = to_csv(mm_rows, ["coreid","identifier","type","format","references"])

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("meta.xml", META_XML)
        zf.writestr("event.csv", event_csv)
        zf.writestr("occurrence.csv", occ_csv)
        zf.writestr("taxon.csv", taxon_csv)
        zf.writestr("multimedia.csv", mm_csv)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Project ZIP import/export
# ---------------------------------------------------------------------------

def export_project_zip(
    project_id: int,
    db: Session,
    include_photos: bool = False,
) -> bytes:
    """Export the entire project as a ZIP (DB + CSV exports + optional photos)."""
    from ..config import DATABASE_PATH

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # manifest
        project = db.query(Project).get(project_id)
        manifest = {
            "version": "1.0",
            "project_id": project_id,
            "project_name": project.name if project else "",
            "exported_at": datetime.utcnow().isoformat(),
            "include_photos": include_photos,
        }
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        # DB snapshot
        zf.write(DATABASE_PATH, arcname="econodex.db")

        # CSV exports
        csvs = {
            "taxa.csv": (_taxa_rows(project_id, db), ["id","parent_taxon_id","scientific_name","rank","common_name","alias","description","created_at","updated_at"]),
            "locations.csv": (_locations_rows(project_id, db), ["id","parent_location_id","name","type","latitude","longitude","altitude","description","created_at","updated_at"]),
            "events.csv": (_events_rows(project_id, db), ["id","location_id","start_date","end_date","description","created_at","updated_at"]),
            "replicates.csv": (_replicates_rows(project_id, db), ["id","event_id","code","method_id","notes","created_at","updated_at"]),
            "records.csv": (_records_rows(project_id, db), ["id","replicate_id","taxon_id","taxon_scientific_name","taxon_alias","individual_count","method_id","date_time","latitude","longitude","notes","created_at","updated_at"]),
            "methods.csv": (_methods_rows(project_id, db), ["id","code","label","description","created_at","updated_at"]),
            "media.csv": (_media_rows(project_id, db), ["id","file_name","relative_path","size_bytes","mime_type","linked_to_type","linked_to_id","is_profile","created_at"]),
        }
        for fname, (rows, fields) in csvs.items():
            zf.writestr(f"csv/{fname}", _write_csv(rows, fields))

        # Photos
        if include_photos and project and project.photos_root_path:
            photos_dir = Path(project.photos_root_path)
            if photos_dir.exists():
                for photo_path in photos_dir.rglob("*"):
                    if photo_path.is_file():
                        try:
                            rel = photo_path.relative_to(photos_dir)
                            zf.write(photo_path, arcname=f"photos/{rel}")
                        except Exception:
                            pass

    return buf.getvalue()
