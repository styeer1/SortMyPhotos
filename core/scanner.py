"""Scanning supported media files in folders."""

from pathlib import Path

from core.metadata import extract_metadata


SUPPORTED_IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".heic",
    ".heif",
    ".bmp",
    ".tiff",
    ".tif",
)

SUPPORTED_VIDEO_EXTENSIONS = (
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".m4v",
    ".3gp",
    ".mpg",
    ".mpeg",
)

MEDIA_EXTENSION_GROUPS = {
    "image": SUPPORTED_IMAGE_EXTENSIONS,
    "video": SUPPORTED_VIDEO_EXTENSIONS,
}


def get_media_type(file_path):
    """Return the media type name for a file or None if unsupported."""
    extension = file_path.suffix.lower()

    for media_type, extensions in MEDIA_EXTENSION_GROUPS.items():
        if extension in extensions:
            return media_type

    return None


def is_supported_image(file_path):
    """Return True if the file is a supported image."""
    return get_media_type(file_path) == "image"


def is_supported_video(file_path):
    """Return True if the file is a supported video."""
    return get_media_type(file_path) == "video"


def is_supported_media(file_path):
    """Return True if the file is a supported media file."""
    return get_media_type(file_path) is not None


def scan_folder(folder_path):
    """Scan a folder and return media files, ignored files, type stats, and errors."""
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    if not folder.is_dir():
        raise NotADirectoryError(f"Path is not a folder: {folder}")

    photos = []
    ignored_files = []
    file_type_counts = {}
    errors = 0
    total_files = 0

    for file_path in folder.iterdir():
        if not file_path.is_file():
            continue

        total_files += 1

        media_type = get_media_type(file_path)

        if media_type is None:
            ignored_files.append(file_path.name)
            continue

        extension = file_path.suffix.lower()
        file_type_counts[extension] = file_type_counts.get(extension, 0) + 1

        try:
            photo = extract_metadata(file_path)
            photo.media_type = media_type  # 👈 přidat
            photos.append(photo)
        except OSError as error:
            errors += 1
            print(f"Could not read file: {file_path.name} ({error})")
        except Exception as error:
            errors += 1
            print(f"Unexpected error for file {file_path.name}: {error}")

    ignored_files.sort()
    file_type_counts = dict(sorted(file_type_counts.items()))

    return photos, errors, ignored_files, file_type_counts, total_files