"""CLI entry point for SortMyPhotos."""

import argparse
import os


RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"

from core.planner import plan_operations
from core.renamer import execute_operations, undo_operations
from core.scanner import scan_folder
from core.sorter import SORT_BY_DAY, SORT_BY_MONTH, SORT_BY_YEAR


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PHOTOS_FOLDER = os.path.join(BASE_DIR, "photos")
LOG_FILE = os.path.join(BASE_DIR, "rename_log.txt")
BACKUP_FILE = os.path.join(BASE_DIR, "rename_backup.json")


def color_text(text, color):
    """Return text wrapped in ANSI color codes."""
    return f"{color}{text}{RESET}"


def success_text(text):
    """Return success-colored text."""
    return color_text(text, GREEN)


def warning_text(text):
    """Return warning-colored text."""
    return color_text(text, YELLOW)


def error_text(text):
    """Return error-colored text."""
    return color_text(text, RED)


def info_text(text):
    """Return info-colored text."""
    return color_text(text, CYAN)


def section_title(text):
    """Return a styled section title."""
    return f"\n{BOLD}{text}{RESET}\n"


def parse_arguments():
    """Parse command-line arguments for CLI mode."""
    parser = argparse.ArgumentParser(
        description="SortMyPhotos CLI tool for renaming and organizing media files."
    )

    parser.add_argument(
        "--path",
        default=PHOTOS_FOLDER,
        help="Path to the folder with media files.",
    )

    parser.add_argument(
        "--action",
        choices=["rename", "organize", "rename_and_organize"],
        help=(
            "Action to perform: "
            "rename = rename files in place, "
            "organize = move/copy into folders and keep original names, "
            "rename_and_organize = move/copy into folders and rename by date."
        ),
    )

    parser.add_argument(
        "--structure",
        choices=["year", "year_month", "year_month_day"],
        help="Folder structure for organize actions.",
    )

    parser.add_argument(
        "--copy",
        action="store_true",
        help="Use copy mode instead of move mode for organize actions.",
    )

    parser.add_argument(
        "--preview",
        action="store_true",
        help="Show preview only without changing files.",
    )

    parser.add_argument(
        "--undo",
        action="store_true",
        help="Undo the last operation.",
    )

    return parser.parse_args()


def print_header():
    """Print the program header."""
    print(f"\n{BOLD}SortMyPhotos{RESET}")
    print("----------------")
    
    
def print_photos(photos, title):
    """Print a list of photos with date and date source."""
    print(f"\n{title}\n")

    for photo in photos:
        print(
            f"{photo.filename} -> "
            f"{photo.date.strftime('%Y-%m-%d %H:%M:%S')} "
            f"[{photo.date_source}]"
        )


def print_preview(rename_plan):
    """Print the planned file operations in a table layout."""
    print("\nPreview:\n")

    old_width = 30
    new_width = 22
    target_width = 30
    source_width = 6
    status_width = 6

    header = (
        f"{'OLD NAME':<{old_width}} "
        f"{'NEW NAME':<{new_width}} "
        f"{'TARGET':<{target_width}} "
        f"{'SRC':<{source_width}} "
        f"{'STATUS':<{status_width}}"
    )
    print(header)
    print("-" * len(header))

    for operation in rename_plan.operations:
        status = "SKIP" if operation.skipped else "OK"

        if operation.operation_mode == "rename":
            target_text = "same folder"
        else:
            target_text = str(operation.target_folder)

        old_name = operation.original_name[:old_width - 1]
        new_name = operation.new_name[:new_width - 1]
        target_text = target_text[:target_width - 1]

        print(
            f"{old_name:<{old_width}} "
            f"{new_name:<{new_width}} "
            f"{target_text:<{target_width}} "
            f"{operation.date_source:<{source_width}} "
            f"{status:<{status_width}}"
        )


def print_conflicts(conflicts):
    """Print detected naming conflicts."""
    print(section_title("Conflicts were found:"))

    for conflict in conflicts:
        print(error_text(f"- {conflict}"))


def print_ignored_files(ignored_files):
    """Print ignored unsupported files."""
    if not ignored_files:
        return

    print(section_title("Ignored unsupported files:"))

    for file_name in ignored_files:
        print(warning_text(f"- {file_name}"))


def print_file_type_stats(file_type_counts):
    """Print statistics for supported file types."""
    if not file_type_counts:
        return

    print(section_title("Supported file type statistics:"))

    for extension, count in file_type_counts.items():
        print(info_text(f"{extension}: {count}"))


def print_stats(stats):
    """Print summary statistics for the current run."""
    print(section_title("Run statistics:"))
    print(info_text(f"Files found: {stats.files_found}"))
    print(info_text(f"EXIF dates: {stats.exif_dates}"))
    print(info_text(f"File dates: {stats.file_dates}"))
    print(info_text(f"Planned operations: {stats.planned_operations}"))
    print(info_text(f"Skipped: {stats.skipped}"))
    print(info_text(f"Ignored unsupported files: {stats.ignored_files}"))
    print(info_text(f"Conflicts: {stats.conflicts}"))
    print(info_text(f"Errors: {stats.errors}"))


def print_operation_summary(rename_plan):
    """Print a short operation summary before confirmation."""
    total_files = len(rename_plan.operations)
    skipped_files = sum(1 for operation in rename_plan.operations if operation.skipped)
    active_files = total_files - skipped_files

    operation_mode = (
        rename_plan.operations[0].operation_mode
        if rename_plan.operations
        else "unknown"
    )
    naming_mode = (
        rename_plan.operations[0].naming_mode
        if rename_plan.operations
        else "unknown"
    )

    print(section_title("Operation summary:"))
    print(info_text(f"Files to process: {total_files}"))
    print(info_text(f"Files with changes: {active_files}"))
    print(info_text(f"Files skipped: {skipped_files}"))
    print(info_text(f"Operation mode: {operation_mode}"))
    print(info_text(f"Naming mode: {naming_mode}"))


def print_completion_summary(rename_plan):
    """Print a short summary after successful execution."""
    total_files = len(rename_plan.operations)
    skipped_files = sum(1 for operation in rename_plan.operations if operation.skipped)
    changed_files = total_files - skipped_files

    print(section_title("Completed operation summary:"))
    print(success_text(f"Processed files: {total_files}"))
    print(success_text(f"Changed files: {changed_files}"))
    print(success_text(f"Skipped files: {skipped_files}"))


def get_sort_mode_label(sort_mode):
    """Return a user-friendly label for the selected folder structure."""
    labels = {
        SORT_BY_YEAR: "YEAR",
        SORT_BY_MONTH: "YEAR/MONTH",
        SORT_BY_DAY: "YEAR/MONTH/DAY",
    }
    return labels.get(sort_mode, sort_mode)


def get_action_label(action):
    """Return a user-friendly label for the selected action."""
    labels = {
        "rename_photos": "Rename photos",
        "organize_photos": "Organize photos into folders",
        "rename_and_organize": "Rename and organize photos",
        "undo": "Undo last operation",
    }
    return labels.get(action, action)


def ask_action():
    """Ask the user what they want to do."""
    print("\nChoose action:")
    print("1 - Rename photos")
    print("2 - Organize photos into folders")
    print("3 - Rename and organize photos")
    print("4 - Undo last operation")

    choice = input("Enter choice (1/2/3/4): ").strip()

    if choice == "1":
        return "rename_photos"
    if choice == "2":
        return "organize_photos"
    if choice == "3":
        return "rename_and_organize"
    if choice == "4":
        return "undo"

    print(error_text("Invalid choice."))
    return None


def ask_sort_mode():
    """Ask the user which folder structure should be used."""
    print("\nChoose folder structure:")
    print("1 - YEAR")
    print("2 - YEAR/MONTH")
    print("3 - YEAR/MONTH/DAY")

    choice = input("Enter choice (1/2/3): ").strip()

    if choice == "1":
        return SORT_BY_YEAR
    if choice == "2":
        return SORT_BY_MONTH
    if choice == "3":
        return SORT_BY_DAY

    print("Invalid choice. Defaulting to YEAR.")
    return SORT_BY_YEAR


def print_selected_options(action, sort_mode=None, operation_mode=None):
    """Print a summary of the selected options."""
    print(section_title("Selected options:"))
    print(info_text(f"Action: {get_action_label(action)}"))

    if sort_mode is not None:
        print(info_text(f"Folder structure: {get_sort_mode_label(sort_mode)}"))

    if operation_mode is not None:
        print(info_text(f"File operation: {operation_mode}"))


def resolve_modes_from_action(action):
    """Map the selected action to internal core modes."""
    if action == "rename_photos":
        return "rename", "rename_by_date"

    if action == "organize_photos":
        return "move", "keep_original_name"

    if action == "rename_and_organize":
        return "move", "rename_by_date"

    raise ValueError(f"Unsupported action: {action}")


def resolve_cli_action(action):
    """Map CLI action names to internal action names."""
    mapping = {
        "rename": "rename_photos",
        "organize": "organize_photos",
        "rename_and_organize": "rename_and_organize",
    }
    return mapping.get(action)


def apply_copy_mode_if_needed(action, operation_mode, args):
    """Override operation mode with copy for organize actions when requested."""
    if not args.copy:
        return operation_mode

    if action in {"organize_photos", "rename_and_organize"}:
        return "copy"

    return operation_mode


def validate_cli_arguments(args):
    """Validate command-line argument combinations."""
    if args.undo and args.action:
        raise ValueError("Cannot use --undo together with --action.")

    if args.undo and args.structure:
        raise ValueError("Cannot use --undo together with --structure.")

    if args.undo and args.copy:
        raise ValueError("Cannot use --undo together with --copy.")

    if args.action == "rename" and args.structure:
        raise ValueError("The --structure option can only be used with organize actions.")

    if args.action == "rename" and args.copy:
        raise ValueError("The --copy option can only be used with organize actions.")

    if args.action in {"organize", "rename_and_organize"} and not args.structure:
        raise ValueError(
            "The --structure option is required for organize actions in command-line mode."
        )


def handle_undo(ask_for_confirmation=True):
    """Handle undo flow."""
    if ask_for_confirmation:
        confirmation = input(
            "Do you really want to restore the last operation? (yes/no): "
        ).strip().lower()

        if confirmation != "yes":
            print("Undo was cancelled.")
            return

    undo_success = undo_operations(BACKUP_FILE)

    if undo_success:
        print("\nUndo completed successfully.")


def main():
    """Run the command-line interface."""
    try:
        args = parse_arguments()
        validate_cli_arguments(args)
        print_header()

        if args.undo:
            handle_undo(args.path, ask_for_confirmation=False)
            return

        if args.action:
            action = resolve_cli_action(args.action)
        else:
            action = ask_action()

        if action is None:
            return

        if action == "undo":
            handle_undo(PHOTOS_FOLDER, ask_for_confirmation=True)
            return

        sort_mode = None

        if action in {"organize_photos", "rename_and_organize"}:

            if args.structure:
                structure_map = {
                    "year": SORT_BY_YEAR,
                    "year_month": SORT_BY_MONTH,
                    "year_month_day": SORT_BY_DAY,
                }
                sort_mode = structure_map.get(args.structure)
            else:
                sort_mode = ask_sort_mode()

        operation_mode, naming_mode = resolve_modes_from_action(action)
        operation_mode = apply_copy_mode_if_needed(action, operation_mode, args)

        print_selected_options(action, sort_mode, operation_mode)

        photos, scan_errors, ignored_files, file_type_counts, total_files = scan_folder(args.path)
                
        if not photos:
            print(warning_text("No supported media files were found in the folder."))
            print_ignored_files(ignored_files)
            return

        print_photos(photos, "Photos before sorting:")
        print_file_type_stats(file_type_counts)
        print_ignored_files(ignored_files)

        if sort_mode is None:
            sort_mode = SORT_BY_YEAR

        rename_plan = plan_operations(
            photos,
            args.path,
            scan_errors,
            ignored_files,
            total_files,
            sort_mode,
            operation_mode,
            naming_mode,
        )

        print_photos(rename_plan.photos, "Photos after sorting:")
        print_preview(rename_plan)
        print_stats(rename_plan.stats)

        if rename_plan.conflicts:
            print_conflicts(rename_plan.conflicts)
            print(error_text("\nOperation was cancelled for safety reasons."))
            return

        print_operation_summary(rename_plan)

        if args.preview:
            print("\nPreview mode enabled. No files will be changed.")
            return

        preview_only = input(
            "\nDo you want preview only without file changes? (yes/no): "
        ).strip().lower()

        if preview_only == "yes":
            print(warning_text("Program finished without changing files."))
            return

        confirmation = input(
            "\nDo you want to continue? (yes/no): "
        ).strip().lower()

        if confirmation != "yes":
            print(warning_text("Operation was cancelled."))
            return

        execute_operations(
            rename_plan,
            args.path,
            LOG_FILE,
            BACKUP_FILE,
        )

        print(success_text("\nDone."))
        print_completion_summary(rename_plan)
        print(success_text(f"Log saved to: {LOG_FILE}"))
        print(success_text(f"Backup saved to: {BACKUP_FILE}"))

    except FileNotFoundError as error:
        print(error_text(f"Error: {error}"))
    except NotADirectoryError as error:
        print(error_text(f"Error: {error}"))
    except PermissionError as error:
        print(error_text(f"Permission error: {error}"))
    except OSError as error:
        print(error_text(f"System error: {error}"))
    except Exception as error:
        print(error_text(f"Unexpected program error: {error}"))


if __name__ == "__main__":
    main()