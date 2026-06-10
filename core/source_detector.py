"""Source detection for source-based rename formats."""

from core.models import PhotoFile


CAMERA_MAKE_MAP = {
    "apple": "iphone",
    "samsung": "samsung",
    "xiaomi": "xiaomi",
    "redmi": "xiaomi",
    "poco": "xiaomi",
    "huawei": "huawei",
    "honor": "honor",
    "oneplus": "oneplus",
    "google": "pixel",
    "motorola": "motorola",
    "nokia": "nokia",
    "sony": "sony",
    "lg": "lg",
    "oppo": "oppo",
    "vivo": "vivo",
    "realme": "realme",
    "asus": "asus",
    "panasonic": "panasonic",
    "canon": "canon",
    "nikon": "nikon",
    "fujifilm": "fujifilm",
    "olympus": "olympus",
    "leica": "leica",
    "gopro": "gopro",
    "dji": "dji",
}


def detect_source_prefix(photo: PhotoFile) -> str:
    """Return a source prefix for source-based rename format."""
    filename_lower = photo.filename.lower()
    stem_lower = photo.stem.lower()
    camera_make_lower = photo.camera_make.lower().strip()

    if (
        (filename_lower.startswith("img-") or filename_lower.startswith("vid-"))
        and "-wa" in stem_lower
    ):
        return "whatsapp"

    if filename_lower.startswith("signal-"):
        return "signal"

    if filename_lower.startswith("received_"):
        return "messenger"

    screenshot_prefixes = (
        "screenshot",
        "screen_shot",
        "screen-shot",
    )

    if filename_lower.startswith(screenshot_prefixes):
        return "screenshot"

    for make_text, normalized_prefix in CAMERA_MAKE_MAP.items():
        if make_text in camera_make_lower:
            return normalized_prefix

    # fallback podle typu souboru
    if photo.media_type == "video":
        return "video"

    return "photo"