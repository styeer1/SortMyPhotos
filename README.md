# SortMyPhotos

Simple offline desktop tool for organizing photos and videos by date.

SortMyPhotos scans a folder with photos and videos and allows you to preview and safely apply operations such as renaming files or organizing them into date-based folders.

The application is designed to be safe and transparent. Every operation can be previewed before execution, and a backup file is created to allow undoing the last operation.

---

# Features

### Rename photos

Rename files using their photo date.

Supported formats:

* `Date (YYYYMMDD_001)`
* `Date and time (YYYYMMDD_HHMMSS_001)`
* `Short date (YYMMDD_001)`
* `Source and date (source_YYYYMMDD_001)`

Examples:

```
20240321_001.jpg
20240321_153045_001.jpg
240321_001.jpg
iphone_20240321_001.jpg
whatsapp_20240321_001.jpg
```

---

### Organize photos

Move or copy files into date-based folders.

Supported folder structures:

```
YEAR
YEAR / MONTH
YEAR / MONTH / DAY
```

Example:

```
2024/
2024/03/
2024/03/21/
```

Files can be either:

* moved to new folders
* copied while keeping the originals

---

### Rename and organize

Combine both operations:

* rename files
* place them into date-based folders

Example result:

```
2024/03/21/20240321_001.jpg
2024/03/21/20240321_002.jpg
```

---

### Source detection

The application can automatically detect the source of some files.

Supported sources:

* WhatsApp
* Signal
* Messenger
* Screenshots
* Camera manufacturer (iPhone, Samsung, Xiaomi, etc.)

Examples:

```
whatsapp_20240321_001.jpg
signal_20260314_001.jpg
messenger_20240321_001.jpg
screenshot_20240321_001.png
iphone_20240321_001.jpg
photo_20240321_001.jpg
```

If the source cannot be detected, the prefix `photo` is used.

---

### Preview before execution

All operations are displayed in a preview table before they are applied.

The preview shows:

* original file name
* new file name
* detected date
* date source (EXIF or file date)
* target folder
* operation status

This allows you to verify everything before modifying any files.

---

### Undo last operation

The application can restore the previous state after the last operation.

Undo is supported for:

* rename operations
* move operations

Undo is **not needed for copy mode**, because the original files remain unchanged.

Undo uses a backup file created during execution.

---

# Supported file types

### Images

```
.jpg
.jpeg
.png
.webp
.heic
.heif
.bmp
.tiff
.tif
```

### Videos

```
.mp4
.mov
.avi
.mkv
.m4v
.3gp
.mpg
.mpeg
```

---

# Date detection

The application tries to determine the correct date using the following priority:

1. EXIF metadata (preferred)
2. File modification date

The preview shows whether the date came from:

```
EXIF
FILE
```

---

# Safety features

SortMyPhotos includes several safety mechanisms:

* preview before execution
* conflict detection
* duplicate name protection
* backup file for undo
* automatic stopping if a risky situation is detected

A log file is also created for every execution.

---

# How to use

1. Select an **input folder** containing photos or videos.
2. Choose the desired **action**.
3. Adjust the **options** if necessary.
4. Click **Preview**.
5. Review the planned operations.
6. Click **Execute** to apply the changes.

---

# Technologies

The application is built using:

* Python
* PySide6 (Qt GUI)
* Pillow (EXIF metadata reading)

---

# License

This project is currently under development.

License will be defined in the future.
