"""Metadata extraction for media files."""

import os
from datetime import datetime
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS

from core.models import PhotoFile


EXIF_SUPPORTED_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".tiff",
    ".tif",
    ".heic",
    ".heif",
)


def supports_exif_date(file_path):
    """Return True if the file type can potentially contain readable EXIF date data."""
    return file_path.suffix.lower() in EXIF_SUPPORTED_EXTENSIONS


def _read_exif_fields(photo_path):
    """Return EXIF fields as a dictionary or an empty dict if unavailable."""
    if not supports_exif_date(photo_path):
        return {}

    try:
        with Image.open(photo_path) as image:
            exif_data = image.getexif()

        if not exif_data:
            return {}

        exif_fields = {}

        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            exif_fields[tag_name] = value

        return exif_fields

    except UnidentifiedImageError:
        print(f"File is not a valid image: {photo_path}")
    except OSError as error:
        print(f"Error opening file {photo_path}: {error}")
    except Exception as error:
        print(f"Unexpected EXIF read error in {photo_path}: {error}")

    return {}


def get_exif_date(photo_path):
    """Try to read the photo date from EXIF. Return None if unavailable."""
    exif_fields = _read_exif_fields(photo_path)

    if not exif_fields:
        return None

    possible_exif_fields = [
        "DateTimeOriginal",
        "DateTimeDigitized",
        "DateTime",
    ]

    for field_name in possible_exif_fields:
        if field_name in exif_fields:
            value = exif_fields[field_name]

            if isinstance(value, str):
                try:
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                except ValueError:
                    print(f"Invalid EXIF date format: {photo_path}")
                    return None

    return None


def get_exif_make(photo_path):
    """Try to read camera maker from EXIF. Return empty string if unavailable."""
    exif_fields = _read_exif_fields(photo_path)

    if not exif_fields:
        return ""

    make_value = exif_fields.get("Make", "")

    if isinstance(make_value, bytes):
        try:
            make_value = make_value.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    if isinstance(make_value, str):
        return make_value.strip()

    return ""


def get_file_date(photo_path):
    """Return the file modification date."""
    modified_time = os.path.getmtime(photo_path)
    return datetime.fromtimestamp(modified_time)


def extract_metadata(photo_path):
    """Build and return a PhotoFile object using EXIF or file date fallback."""
    photo_path = Path(photo_path)

    exif_date = get_exif_date(photo_path)
    camera_make = get_exif_make(photo_path)

    if exif_date is not None:
        photo_date = exif_date
        date_source = "EXIF"
    else:
        photo_date = get_file_date(photo_path)
        date_source = "FILE"

    return PhotoFile(
        path=photo_path,
        filename=photo_path.name,
        extension=photo_path.suffix,
        date=photo_date,
        date_source=date_source,
        camera_make=camera_make,
    )