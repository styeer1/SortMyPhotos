"""Data models for SortMyPhotos."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class PhotoFile:
    """Represents one scanned photo file."""

    path: Path
    filename: str
    extension: str
    date: datetime
    date_source: str
    camera_make: str = ""
    media_type: str = "image"   # 👈 NOVÉ

    @property
    def full_path(self) -> Path:
        return self.path

    @property
    def stem(self) -> str:
        return self.path.stem


@dataclass
class RenameOperation:
    """Represents one planned file operation."""

    source_path: Path
    target_path: Path
    target_folder: Path
    original_name: str
    new_name: str
    date_source: str
    photo_date: datetime
    operation_mode: str
    naming_mode: str
    skipped: bool = False
    skip_reason: str = ""


@dataclass
class RunStats:
    """Represents summary statistics for one program run."""

    files_found: int = 0
    exif_dates: int = 0
    file_dates: int = 0
    planned_operations: int = 0
    skipped: int = 0
    conflicts: int = 0
    errors: int = 0
    ignored_files: int = 0


@dataclass
class RenamePlan:
    """Represents the full rename plan."""

    photos: list[PhotoFile] = field(default_factory=list)
    operations: list[RenameOperation] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    stats: RunStats = field(default_factory=RunStats)