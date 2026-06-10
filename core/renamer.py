"""Executing rename and undo operations."""

import json
import shutil
from datetime import datetime
from pathlib import Path


def write_rename_log(rename_plan, log_path):
    """Append the rename plan to the log file."""
    run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = Path(log_path)

    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write("=" * 50 + "\n")
        log_file.write(f"Run time: {run_time}\n")
        log_file.write("-" * 50 + "\n")

        for operation in rename_plan.operations:
            log_file.write(
                f"{operation.operation_mode.upper()} | "
                f"{operation.naming_mode.upper()} | "
                f"{operation.original_name} -> {operation.new_name} | "
                f"target folder: {operation.target_folder} "
                f"[{operation.date_source}]\n"
            )

        log_file.write("\n")


def write_backup_file(rename_plan, backup_path, base_folder):
    """Save base folder and file operations into a backup JSON file."""
    backup_path = Path(backup_path)
    base_folder = Path(base_folder).resolve()

    backup_data = {
        "base_folder": str(base_folder),
        "operations": [],
    }

    for operation in rename_plan.operations:
        backup_data["operations"].append(
            {
                "operation_mode": operation.operation_mode,
                "naming_mode": operation.naming_mode,
                "old_path": str(operation.source_path),
                "new_path": str(operation.target_path),
                "old_name": operation.original_name,
                "new_name": operation.new_name,
            }
        )

    with backup_path.open("w", encoding="utf-8") as backup_file:
        json.dump(backup_data, backup_file, indent=4, ensure_ascii=False)


def _report_progress(progress_callback, current, total, message):
    """Call optional progress callback."""
    if progress_callback is not None:
        progress_callback(current, total, message)


def execute_rename_in_place(rename_plan, base_folder, progress_callback=None):
    """Rename files inside the same folder using a two-phase rename."""
    temp_paths = []
    total_operations = len(rename_plan.operations)

    for index, operation in enumerate(rename_plan.operations):
        source_path = operation.source_path

        if operation.skipped:
            message = f"Skipped: {operation.original_name}"
            print(f"Skipped: {operation.original_name} ({operation.skip_reason})")
            temp_paths.append(None)
            _report_progress(
                progress_callback,
                index + 1,
                total_operations,
                message,
            )
            continue

        temp_name = f"__tmp__{index}{source_path.suffix}"
        temp_path = Path(base_folder) / temp_name

        if temp_path.exists():
            raise FileExistsError(
                f"Temporary file already exists: {temp_name}"
            )

        source_path.rename(temp_path)
        temp_paths.append(temp_path)

    for index, operation in enumerate(rename_plan.operations):
        if temp_paths[index] is None:
            continue

        final_path = operation.source_path.parent / operation.new_name
        temp_paths[index].rename(final_path)

        message = f"Renamed: {operation.original_name} -> {final_path.name}"
        print(
            f"[{index + 1}/{total_operations}] "
            f"Renamed in place: {operation.original_name} -> {final_path.name}"
        )
        _report_progress(
            progress_callback,
            index + 1,
            total_operations,
            message,
        )


def execute_move_to_folders(rename_plan, base_folder, progress_callback=None):
    """Move and rename files into target folders using a two-phase rename."""
    base_folder = Path(base_folder)
    temp_paths = []
    total_operations = len(rename_plan.operations)

    for index, operation in enumerate(rename_plan.operations):
        source_path = operation.source_path

        if operation.skipped:
            message = f"Skipped: {operation.original_name}"
            print(f"Skipped: {operation.original_name} ({operation.skip_reason})")
            temp_paths.append(None)
            _report_progress(
                progress_callback,
                index + 1,
                total_operations,
                message,
            )
            continue

        temp_name = f"__tmp__{index}{source_path.suffix}"
        temp_path = base_folder / temp_name

        if temp_path.exists():
            raise FileExistsError(
                f"Temporary file already exists: {temp_name}"
            )

        source_path.rename(temp_path)
        temp_paths.append(temp_path)

    for operation in rename_plan.operations:
        operation.target_folder.mkdir(parents=True, exist_ok=True)

    for index, operation in enumerate(rename_plan.operations):
        if temp_paths[index] is None:
            continue

        temp_paths[index].rename(operation.target_path)

        if operation.naming_mode == "keep_original_name":
            message = f"Moved: {operation.original_name}"
            print(
                f"[{index + 1}/{total_operations}] "
                f"Moved: {operation.original_name} -> {operation.target_path}"
            )
        else:
            message = f"Moved and renamed: {operation.original_name}"
            print(
                f"[{index + 1}/{total_operations}] "
                f"Moved and renamed: {operation.original_name} -> {operation.target_path}"
            )

        _report_progress(
            progress_callback,
            index + 1,
            total_operations,
            message,
        )


def execute_copy_to_folders(rename_plan, progress_callback=None):
    """Copy and rename files into target folders without modifying originals."""
    total_operations = len(rename_plan.operations)

    for index, operation in enumerate(rename_plan.operations):
        if operation.skipped:
            message = f"Skipped: {operation.original_name}"
            print(
                f"[{index + 1}/{total_operations}] "
                f"Skipped: {operation.original_name} ({operation.skip_reason})"
            )
            _report_progress(
                progress_callback,
                index + 1,
                total_operations,
                message,
            )
            continue

        operation.target_folder.mkdir(parents=True, exist_ok=True)
        shutil.copy2(operation.source_path, operation.target_path)

        if operation.naming_mode == "keep_original_name":
            message = f"Copied: {operation.original_name}"
            print(
                f"[{index + 1}/{total_operations}] "
                f"Copied: {operation.original_name} -> {operation.target_path}"
            )
        else:
            message = f"Copied and renamed: {operation.original_name}"
            print(
                f"[{index + 1}/{total_operations}] "
                f"Copied and renamed: {operation.original_name} -> {operation.target_path}"
            )

        _report_progress(
            progress_callback,
            index + 1,
            total_operations,
            message,
        )


def execute_file_operations(rename_plan, base_folder, progress_callback=None):
    """Execute planned file operations according to operation mode."""
    if not rename_plan.operations:
        return

    operation_mode = rename_plan.operations[0].operation_mode

    if operation_mode == "rename":
        execute_rename_in_place(rename_plan, base_folder, progress_callback)
        return

    if operation_mode == "move":
        execute_move_to_folders(rename_plan, base_folder, progress_callback)
        return

    if operation_mode == "copy":
        execute_copy_to_folders(rename_plan, progress_callback)
        return

    raise ValueError(f"Unsupported operation mode: {operation_mode}")


def execute_operations(
    rename_plan,
    folder_path,
    log_path,
    backup_path,
    progress_callback=None,
):
    """Write backup, write log, and execute file operations."""
    write_backup_file(rename_plan, backup_path, folder_path)
    write_rename_log(rename_plan, log_path)
    execute_file_operations(rename_plan, folder_path, progress_callback)


def remove_empty_parent_folders(folder_path, stop_folder):
    """Remove empty parent folders up to the stop folder."""
    folder_path = Path(folder_path)
    stop_folder = Path(stop_folder).resolve()

    current_folder = folder_path.resolve()

    while current_folder != stop_folder:
        if not current_folder.exists() or not current_folder.is_dir():
            break

        try:
            current_folder.rmdir()
        except OSError:
            break

        current_folder = current_folder.parent


def _path_is_within(path_to_check: Path, parent_path: Path) -> bool:
    """Return True if path_to_check is inside parent_path or equal to it."""
    try:
        path_to_check.resolve().relative_to(parent_path.resolve())
        return True
    except ValueError:
        return False


def validate_backup_data(backup_data):
    """Validate backup structure and basic path safety before undo."""
    if not isinstance(backup_data, dict):
        raise ValueError(
            "Backup file uses an older or invalid format. "
            "Expected a JSON object with base_folder and operations."
        )

    base_folder_text = backup_data.get("base_folder")
    operations = backup_data.get("operations")

    if not base_folder_text:
        raise ValueError(
            "Backup file does not contain base_folder. "
            "Undo cannot continue safely."
        )

    if operations is None:
        raise ValueError(
            "Backup file does not contain operations. "
            "Undo cannot continue safely."
        )

    if not isinstance(operations, list):
        raise ValueError(
            "Backup file has invalid operations format. "
            "Expected a list of operations."
        )

    if not operations:
        return Path(base_folder_text).resolve(), operations

    base_folder = Path(base_folder_text).resolve()

    for index, item in enumerate(operations, start=1):
        if not isinstance(item, dict):
            raise ValueError(
                f"Backup operation #{index} has invalid format. "
                "Expected an object."
            )

        required_keys = {"operation_mode", "old_path", "new_path", "new_name"}
        missing_keys = required_keys - set(item.keys())

        if missing_keys:
            missing_text = ", ".join(sorted(missing_keys))
            raise ValueError(
                f"Backup operation #{index} is missing required fields: {missing_text}."
            )

        operation_mode = item["operation_mode"]
        old_path = Path(item["old_path"])
        new_path = Path(item["new_path"])

        if operation_mode not in {"rename", "move", "copy"}:
            raise ValueError(
                f"Backup operation #{index} has unsupported operation_mode: "
                f"{operation_mode}"
            )

        if not old_path.is_absolute():
            raise ValueError(
                f"Backup operation #{index} has non-absolute old_path: {old_path}"
            )

        if not new_path.is_absolute():
            raise ValueError(
                f"Backup operation #{index} has non-absolute new_path: {new_path}"
            )

        if operation_mode == "rename":
            if old_path.parent.resolve() != new_path.parent.resolve():
                raise ValueError(
                    f"Backup operation #{index} is invalid for rename mode: "
                    "old_path and new_path must stay in the same folder."
                )

        if operation_mode in {"move", "copy"}:
            if not _path_is_within(new_path.parent, base_folder):
                raise ValueError(
                    f"Backup operation #{index} is outside base_folder: {new_path}"
                )

    return base_folder, operations


def undo_operations(backup_path):
    """Restore original file paths using the backup JSON file."""
    backup_path = Path(backup_path)

    if not backup_path.exists():
        raise FileNotFoundError(
            f"Backup file does not exist: {backup_path}"
        )

    with backup_path.open("r", encoding="utf-8") as backup_file:
        backup_data = json.load(backup_file)

    base_folder, operations = validate_backup_data(backup_data)

    if not operations:
        print("Backup file is empty.")
        return False

    operation_mode = operations[0].get("operation_mode", "move")

    if operation_mode == "copy":
        print("\nUndo is not needed for copy mode.")
        print("Original files were not modified.")
        return False

    conflicts = []

    for item in operations:
        old_path = Path(item["old_path"])
        new_path = Path(item["new_path"])

        if operation_mode == "rename":
            current_path = old_path.parent / item["new_name"]
            original_path = old_path
        else:
            current_path = new_path
            original_path = old_path

        if not current_path.exists():
            conflicts.append(
                f"File for restore does not exist: {current_path}"
            )

        if original_path.exists() and original_path != current_path:
            conflicts.append(
                f"Original path is already occupied: {original_path}"
            )

    if conflicts:
        print("\nUndo cannot continue because of these problems:\n")
        for conflict in conflicts:
            print(f"- {conflict}")
        return False

    temp_paths = []

    for index, item in enumerate(operations):
        old_path = Path(item["old_path"])
        new_path = Path(item["new_path"])

        if operation_mode == "rename":
            current_path = old_path.parent / item["new_name"]
        else:
            current_path = new_path

        if old_path == current_path:
            print(f"Skipped: {old_path.name} (already restored)")
            temp_paths.append(None)
            continue

        temp_name = f"__undo_tmp__{index}{current_path.suffix}"
        temp_path = current_path.parent / temp_name

        if temp_path.exists():
            raise FileExistsError(
                f"Temporary undo file already exists: {temp_path.name}"
            )

        current_path.rename(temp_path)
        temp_paths.append((temp_path, old_path, current_path.parent))

    for temp_item in temp_paths:
        if temp_item is None:
            continue

        temp_path, old_path, source_folder = temp_item
        old_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.rename(old_path)

        remove_empty_parent_folders(source_folder, base_folder)

        print(f"Restored: {temp_path.name} -> {old_path}")

    return True