"""Sorting files into folders."""

from pathlib import Path


SORT_BY_YEAR = "year"
SORT_BY_MONTH = "year_month"
SORT_BY_DAY = "year_month_day"

SUPPORTED_SORT_MODES = {
    SORT_BY_YEAR,
    SORT_BY_MONTH,
    SORT_BY_DAY,
}


def build_target_folder(base_folder, photo_date, sort_mode):
    """Return the target folder based on the selected sort mode."""
    base_folder = Path(base_folder)

    if sort_mode == SORT_BY_YEAR:
        return base_folder / photo_date.strftime("%Y")

    if sort_mode == SORT_BY_MONTH:
        return (
            base_folder
            / photo_date.strftime("%Y")
            / photo_date.strftime("%m")
        )

    if sort_mode == SORT_BY_DAY:
        return (
            base_folder
            / photo_date.strftime("%Y")
            / photo_date.strftime("%m")
            / photo_date.strftime("%d")
        )

    raise ValueError(f"Unsupported sort mode: {sort_mode}")