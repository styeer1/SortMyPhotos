"""Planning rename operations."""

from core.models import RenameOperation, RenamePlan, RunStats
from core.sorter import build_target_folder, SORT_BY_YEAR
from core.source_detector import detect_source_prefix


def sort_photos(photos):
    """Return photos sorted by date."""
    return sorted(photos, key=lambda photo: photo.date)


def build_rename_operations(
    photos,
    folder_path,
    sort_mode=SORT_BY_YEAR,
    operation_mode="move",
    naming_mode="rename_by_date",
):
    """Build rename operations based on selected naming mode."""
    operations = []
    name_counters = {}

    for photo in photos:
        date_for_name = photo.date.strftime("%Y%m%d")

        if naming_mode == "rename_by_date":
            base_name = date_for_name

        elif naming_mode == "rename_by_datetime":
            time_part = photo.date.strftime("%H%M%S")
            base_name = f"{date_for_name}_{time_part}"

        elif naming_mode == "rename_by_short_date":
            short_date = photo.date.strftime("%y%m%d")
            base_name = short_date

        elif naming_mode == "rename_by_source_date":
            source_prefix = detect_source_prefix(photo)
            base_name = f"{source_prefix}_{date_for_name}"

        elif naming_mode == "keep_original_name":
            base_name = None

        else:
            raise ValueError(f"Unsupported naming mode: {naming_mode}")

        if naming_mode == "keep_original_name":
            new_name = photo.filename
        else:
            counter_key = base_name
            name_counters[counter_key] = name_counters.get(counter_key, 0) + 1
            sequence = name_counters[counter_key]
            new_name = f"{base_name}_{sequence:03d}{photo.extension}"

        if operation_mode == "rename":
            target_folder = photo.path.parent
        else:
            target_folder = build_target_folder(folder_path, photo.date, sort_mode)

        target_path = target_folder / new_name

        skipped = (
            photo.filename == new_name
            and photo.path.parent == target_folder
        )

        operation = RenameOperation(
            source_path=photo.path,
            target_path=target_path,
            target_folder=target_folder,
            original_name=photo.filename,
            new_name=new_name,
            date_source=photo.date_source,
            photo_date=photo.date,
            operation_mode=operation_mode,
            naming_mode=naming_mode,
            skipped=skipped,
            skip_reason="Already has the correct name in the correct folder."
            if skipped
            else "",
        )
        operations.append(operation)

    return operations


def check_name_conflicts(operations):
    """Check for duplicate target names and existing file conflicts."""
    conflicts = []
    planned_targets = set()
    source_paths = {operation.source_path.resolve() for operation in operations}

    for operation in operations:
        target_key = str(operation.target_path.resolve()).lower()

        if target_key in planned_targets:
            conflicts.append(
                f"Duplicate target path in plan: {operation.target_path}"
            )
        else:
            planned_targets.add(target_key)

        target_exists = operation.target_path.exists()
        target_is_source_file = operation.target_path.resolve() in source_paths

        if (
            target_exists
            and not operation.skipped
            and not target_is_source_file
        ):
            conflicts.append(
                f"Target file already exists: {operation.target_path}"
            )

    return conflicts


def build_run_stats(
    photos,
    operations,
    conflicts,
    scan_errors,
    ignored_files=None,
    total_files=0,
):
    """Build summary statistics for the current run."""
    stats = RunStats()
    stats.files_found = total_files
    stats.exif_dates = sum(1 for photo in photos if photo.date_source == "EXIF")
    stats.file_dates = sum(1 for photo in photos if photo.date_source == "FILE")
    stats.planned_operations = len(operations)
    stats.skipped = sum(1 for operation in operations if operation.skipped)
    stats.conflicts = len(conflicts)
    stats.errors = scan_errors
    stats.ignored_files = len(ignored_files or [])
    return stats


def plan_operations(
    photos,
    folder_path,
    scan_errors=0,
    ignored_files=None,
    total_files=0,
    sort_mode=SORT_BY_YEAR,
    operation_mode="move",
    naming_mode="rename_by_date",
):
    """Prepare and validate rename operations."""
    if operation_mode == "rename" and naming_mode == "keep_original_name":
        raise ValueError(
            "Invalid combination: rename in place cannot be used with keep original name."
        )

    sorted_photos = sort_photos(photos)
    operations = build_rename_operations(
        sorted_photos,
        folder_path,
        sort_mode,
        operation_mode,
        naming_mode,
    )
    conflicts = check_name_conflicts(operations)
    stats = build_run_stats(
        sorted_photos,
        operations,
        conflicts,
        scan_errors,
        ignored_files,
        total_files,
    )
    return RenamePlan(
        photos=sorted_photos,
        operations=operations,
        conflicts=conflicts,
        stats=stats,
    )