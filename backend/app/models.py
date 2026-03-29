"""SQLAlchemy ORM models for EcoNodeX."""
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, CheckConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


def _now():
    return datetime.utcnow()


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    photos_root_path = Column(String(512))
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    locations = relationship("Location", back_populates="project", cascade="all, delete-orphan")
    taxa = relationship("Taxon", back_populates="project", cascade="all, delete-orphan")
    methods = relationship("Method", back_populates="project", cascade="all, delete-orphan")
    sampling_events = relationship("SamplingEvent", back_populates="project", cascade="all, delete-orphan")
    media = relationship("Media", back_populates="project", cascade="all, delete-orphan")
    merge_logs = relationship("MergeLog", back_populates="project", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Location  (self-referential tree)
# ---------------------------------------------------------------------------

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    parent_location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"))
    name = Column(String(255), nullable=False)
    type = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    description = Column(Text)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    project = relationship("Project", back_populates="locations")
    parent = relationship("Location", remote_side="Location.id", back_populates="children")
    children = relationship("Location", back_populates="parent", cascade="all, delete-orphan")
    sampling_events = relationship("SamplingEvent", back_populates="location")
    media = relationship(
        "Media",
        primaryjoin="and_(Media.linked_to_type=='location', foreign(Media.linked_to_id)==Location.id)",
        viewonly=True,
    )


# ---------------------------------------------------------------------------
# Taxon  (self-referential tree)
# ---------------------------------------------------------------------------

class Taxon(Base):
    __tablename__ = "taxa"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    parent_taxon_id = Column(Integer, ForeignKey("taxa.id", ondelete="SET NULL"))
    scientific_name = Column(String(255), nullable=False)
    rank = Column(String(100), nullable=False)
    common_name = Column(String(255))
    alias = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    project = relationship("Project", back_populates="taxa")
    parent = relationship("Taxon", remote_side="Taxon.id", back_populates="children")
    children = relationship("Taxon", back_populates="parent", cascade="all, delete-orphan")
    occurrence_records = relationship("OccurrenceRecord", back_populates="taxon")
    media = relationship(
        "Media",
        primaryjoin="and_(Media.linked_to_type=='taxon', foreign(Media.linked_to_id)==Taxon.id)",
        viewonly=True,
    )


# ---------------------------------------------------------------------------
# Method  (editable catalog per project)
# ---------------------------------------------------------------------------

class Method(Base):
    __tablename__ = "methods"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False)
    label = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    project = relationship("Project", back_populates="methods")
    replicates = relationship("Replicate", back_populates="method")
    occurrence_records = relationship("OccurrenceRecord", back_populates="method")


# ---------------------------------------------------------------------------
# SamplingEvent
# ---------------------------------------------------------------------------

class SamplingEvent(Base):
    __tablename__ = "sampling_events"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False)
    start_date = Column(String(10), nullable=False)   # ISO date "YYYY-MM-DD"
    end_date = Column(String(10))
    description = Column(Text)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    project = relationship("Project", back_populates="sampling_events")
    location = relationship("Location", back_populates="sampling_events")
    replicates = relationship("Replicate", back_populates="event", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Replicate
# ---------------------------------------------------------------------------

class Replicate(Base):
    __tablename__ = "replicates"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("sampling_events.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False)
    method_id = Column(Integer, ForeignKey("methods.id", ondelete="SET NULL"))
    notes = Column(Text)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    event = relationship("SamplingEvent", back_populates="replicates")
    method = relationship("Method", back_populates="replicates")
    occurrence_records = relationship("OccurrenceRecord", back_populates="replicate", cascade="all, delete-orphan")
    media = relationship(
        "Media",
        primaryjoin="and_(Media.linked_to_type=='record', foreign(Media.linked_to_id)==Replicate.id)",
        viewonly=True,
    )


# ---------------------------------------------------------------------------
# OccurrenceRecord
# ---------------------------------------------------------------------------

class OccurrenceRecord(Base):
    __tablename__ = "occurrence_records"

    id = Column(Integer, primary_key=True, index=True)
    replicate_id = Column(Integer, ForeignKey("replicates.id", ondelete="CASCADE"), nullable=False)
    taxon_id = Column(Integer, ForeignKey("taxa.id", ondelete="RESTRICT"), nullable=False)
    individual_count = Column(Integer, nullable=False, default=0)
    method_id = Column(Integer, ForeignKey("methods.id", ondelete="SET NULL"))
    date_time = Column(String(25))   # ISO datetime string (optional)
    latitude = Column(Float)
    longitude = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    replicate = relationship("Replicate", back_populates="occurrence_records")
    taxon = relationship("Taxon", back_populates="occurrence_records")
    method = relationship("Method", back_populates="occurrence_records")
    media = relationship(
        "Media",
        primaryjoin="and_(Media.linked_to_type=='record', foreign(Media.linked_to_id)==OccurrenceRecord.id)",
        viewonly=True,
    )


# ---------------------------------------------------------------------------
# Media
# ---------------------------------------------------------------------------

LINKED_TO_TYPES = ("taxon", "location", "record", "replicate")


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    relative_path = Column(String(512), nullable=False)
    thumbnail_path = Column(String(512))
    size_bytes = Column(Integer)
    mime_type = Column(String(100))
    exif_json = Column(Text)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)
    linked_to_type = Column(
        String(20),
        CheckConstraint("linked_to_type IN ('taxon','location','record','replicate')"),
    )
    linked_to_id = Column(Integer)
    is_profile = Column(Boolean, default=False)

    project = relationship("Project", back_populates="media")


# ---------------------------------------------------------------------------
# MergeLog
# ---------------------------------------------------------------------------

class MergeLog(Base):
    __tablename__ = "merge_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    source_taxon_id = Column(Integer)   # may be deleted, so no FK
    source_taxon_name = Column(String(255))
    source_taxon_alias = Column(String(255))
    target_taxon_id = Column(Integer, ForeignKey("taxa.id", ondelete="SET NULL"))
    target_taxon_name = Column(String(255))
    records_affected = Column(Integer, default=0)
    media_affected = Column(Integer, default=0)
    backup_path = Column(String(512))
    created_at = Column(DateTime, default=_now)

    project = relationship("Project", back_populates="merge_logs")
    target_taxon = relationship("Taxon")
