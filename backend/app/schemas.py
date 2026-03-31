"""Pydantic v2 schemas for request/response validation."""
from __future__ import annotations
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, field_validator


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class _TimestampMixin(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    photos_root_path: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    photos_root_path: Optional[str] = None


class ProjectOut(_TimestampMixin):
    id: int
    name: str
    description: Optional[str] = None
    photos_root_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------

class LocationCreate(BaseModel):
    project_id: int
    parent_location_id: Optional[int] = None
    name: str
    type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    description: Optional[str] = None


class LocationUpdate(BaseModel):
    parent_location_id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    description: Optional[str] = None


class LocationOut(_TimestampMixin):
    id: int
    project_id: int
    parent_location_id: Optional[int] = None
    name: str
    type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    description: Optional[str] = None
    children: List["LocationOut"] = []


LocationOut.model_rebuild()


# ---------------------------------------------------------------------------
# Taxon
# ---------------------------------------------------------------------------

class TaxonCreate(BaseModel):
    project_id: int
    parent_taxon_id: Optional[int] = None
    scientific_name: str
    rank: str
    common_name: Optional[str] = None
    alias: Optional[str] = None
    description: Optional[str] = None
    is_recordable: bool = False


class TaxonUpdate(BaseModel):
    parent_taxon_id: Optional[int] = None
    scientific_name: Optional[str] = None
    rank: Optional[str] = None
    common_name: Optional[str] = None
    alias: Optional[str] = None
    description: Optional[str] = None
    is_recordable: Optional[bool] = None


class TaxonOut(_TimestampMixin):
    id: int
    project_id: int
    parent_taxon_id: Optional[int] = None
    scientific_name: str
    rank: str
    common_name: Optional[str] = None
    alias: Optional[str] = None
    description: Optional[str] = None
    is_recordable: bool = False
    profile_media_id: Optional[int] = None
    children: List["TaxonOut"] = []


TaxonOut.model_rebuild()


# ---------------------------------------------------------------------------
# Method
# ---------------------------------------------------------------------------

class MethodCreate(BaseModel):
    project_id: int
    code: str
    label: str
    description: Optional[str] = None


class MethodUpdate(BaseModel):
    code: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None


class MethodOut(_TimestampMixin):
    id: int
    project_id: int
    code: str
    label: str
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# SamplingEvent
# ---------------------------------------------------------------------------

class SamplingEventCreate(BaseModel):
    project_id: int
    location_id: int
    start_date: str
    end_date: Optional[str] = None
    description: Optional[str] = None


class SamplingEventUpdate(BaseModel):
    location_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class SamplingEventOut(_TimestampMixin):
    id: int
    project_id: int
    location_id: int
    start_date: str
    end_date: Optional[str] = None
    description: Optional[str] = None
    location_name: Optional[str] = None
    replicate_count: Optional[int] = None


# ---------------------------------------------------------------------------
# Replicate
# ---------------------------------------------------------------------------

class ReplicateCreate(BaseModel):
    event_id: int
    code: str
    method_id: Optional[int] = None
    notes: Optional[str] = None


class ReplicateUpdate(BaseModel):
    code: Optional[str] = None
    method_id: Optional[int] = None
    notes: Optional[str] = None


class ReplicateOut(_TimestampMixin):
    id: int
    event_id: int
    code: str
    method_id: Optional[int] = None
    method_label: Optional[str] = None
    notes: Optional[str] = None
    record_count: Optional[int] = None


# ---------------------------------------------------------------------------
# OccurrenceRecord
# ---------------------------------------------------------------------------

class OccurrenceRecordCreate(BaseModel):
    replicate_id: int
    taxon_id: int
    individual_count: int = 0
    method_id: Optional[int] = None
    date_time: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


class OccurrenceRecordUpdate(BaseModel):
    taxon_id: Optional[int] = None
    individual_count: Optional[int] = None
    method_id: Optional[int] = None
    date_time: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


class OccurrenceRecordOut(_TimestampMixin):
    id: int
    replicate_id: int
    taxon_id: int
    taxon_name: Optional[str] = None
    taxon_alias: Optional[str] = None
    taxon_profile_media_id: Optional[int] = None
    individual_count: int
    method_id: Optional[int] = None
    method_label: Optional[str] = None
    date_time: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Media
# ---------------------------------------------------------------------------

class MediaOut(_TimestampMixin):
    id: int
    project_id: int
    file_name: str
    relative_path: str
    thumbnail_path: Optional[str] = None
    size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    exif_json: Optional[str] = None
    linked_to_type: Optional[str] = None
    linked_to_id: Optional[int] = None
    is_profile: bool = False


class MediaUpdate(BaseModel):
    linked_to_type: Optional[str] = None
    linked_to_id: Optional[int] = None
    is_profile: Optional[bool] = None


# ---------------------------------------------------------------------------
# MergeLog
# ---------------------------------------------------------------------------

class MergeLogOut(_TimestampMixin):
    id: int
    project_id: int
    source_taxon_id: Optional[int] = None
    source_taxon_name: Optional[str] = None
    source_taxon_alias: Optional[str] = None
    target_taxon_id: Optional[int] = None
    target_taxon_name: Optional[str] = None
    records_affected: int = 0
    media_affected: int = 0
    backup_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Merge preview / request
# ---------------------------------------------------------------------------

class MergePreview(BaseModel):
    source_taxon_id: int
    target_taxon_id: int


class MergePreviewOut(BaseModel):
    source_taxon_id: int
    source_taxon_name: str
    source_taxon_alias: Optional[str]
    target_taxon_id: int
    target_taxon_name: str
    records_affected: int
    media_affected: int


class MergeExecute(BaseModel):
    source_taxon_id: int
    target_taxon_id: int
    confirmation: str   # must equal "CONFIRMAR"


# ---------------------------------------------------------------------------
# Analysis request / response
# ---------------------------------------------------------------------------

class AnalysisScope(BaseModel):
    type: str      # "project" | "location" | "event" | "replicate"
    id: Optional[int] = None


class AnalysisRequest(BaseModel):
    project_id: int
    scope: AnalysisScope
    permutations: int = 100   # for species accumulation


class AnalysisResult(BaseModel):
    analysis_type: str
    scope: AnalysisScope
    timestamp: str
    parameters: dict
    results: Any
    plot_b64: Optional[str] = None   # base64 PNG


# ---------------------------------------------------------------------------
# QR / Upload
# ---------------------------------------------------------------------------

class QRResponse(BaseModel):
    upload_url: str
    qr_b64: str   # base64 PNG


class UploadDestination(BaseModel):
    type: str        # taxon | location | record | replicate
    id: int
    label: str


# ---------------------------------------------------------------------------
# Export / Import
# ---------------------------------------------------------------------------

class ExportOptions(BaseModel):
    include_photos: bool = False


class ImportOptions(BaseModel):
    conflict_strategy: str = "skip"   # skip | overwrite
