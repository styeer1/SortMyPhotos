from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class SetupPage(QWidget):
    """Main setup page for selecting action and options."""

    preview_requested = Signal(object, str)
    undo_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()
        self._set_options_stack_stable_height()
        self._update_selected_action_label()
        self._update_options_page()
        self._update_primary_button_text()
        self._update_rename_only_format_help()
        self._update_combined_format_help()

    def _build_ui(self) -> None:
        """Create and arrange widgets for the setup page."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)

        title_label = QLabel("SortMyPhotos")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        source_frame = QFrame()
        source_frame.setFrameShape(QFrame.StyledPanel)
        source_layout = QVBoxLayout()
        source_layout.setContentsMargins(12, 12, 12, 12)
        source_layout.setSpacing(10)
        source_frame.setLayout(source_layout)

        source_title = QLabel("Input folder")
        source_title_font = source_title.font()
        source_title_font.setBold(True)
        source_title.setFont(source_title_font)
        source_title.setToolTip(
            "Select the folder that contains the photos and videos you want to process."
        )
        source_layout.addWidget(source_title)

        source_row = QHBoxLayout()
        source_row.setSpacing(8)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select folder with photos and videos...")
        self.path_input.setToolTip(
            "Path to the folder that will be scanned for supported media files."
        )
        source_row.addWidget(self.path_input)

        self.browse_button = QPushButton("Browse...")
        self.browse_button.setToolTip(
            "Open a folder picker and choose the input folder."
        )
        self.browse_button.clicked.connect(self._choose_folder)
        source_row.addWidget(self.browse_button)

        source_layout.addLayout(source_row)
        main_layout.addWidget(source_frame)

        action_frame = QFrame()
        action_frame.setFrameShape(QFrame.StyledPanel)
        action_layout = QVBoxLayout()
        action_layout.setContentsMargins(12, 12, 12, 12)
        action_layout.setSpacing(10)
        action_frame.setLayout(action_layout)

        action_title = QLabel("Action")
        action_title_font = action_title.font()
        action_title_font.setBold(True)
        action_title.setFont(action_title_font)
        action_title.setToolTip("Choose what the application should do with your files.")
        action_layout.addWidget(action_title)

        self.action_group = QButtonGroup(self)

        self.rename_radio = QRadioButton("Rename photos")
        self.rename_radio.setToolTip(
            "Rename files in the same folder using the photo date."
        )

        self.organize_radio = QRadioButton("Organize photos")
        self.organize_radio.setToolTip(
            "Keep original file names and place files into date-based folders."
        )

        self.rename_and_organize_radio = QRadioButton("Rename and organize")
        self.rename_and_organize_radio.setToolTip(
            "Rename files by date and place them into date-based folders."
        )

        self.undo_radio = QRadioButton("Undo")
        self.undo_radio.setToolTip(
            "Restore the last rename or move operation using the backup file."
        )

        self.action_group.addButton(self.rename_radio)
        self.action_group.addButton(self.organize_radio)
        self.action_group.addButton(self.rename_and_organize_radio)
        self.action_group.addButton(self.undo_radio)

        self.rename_radio.setChecked(True)

        action_layout.addWidget(self.rename_radio)
        action_layout.addWidget(self.organize_radio)
        action_layout.addWidget(self.rename_and_organize_radio)
        action_layout.addWidget(self.undo_radio)

        self.action_group.buttonClicked.connect(self._on_action_changed)

        main_layout.addWidget(action_frame)

        self.selected_action_label = QLabel()
        self.selected_action_label.setToolTip(
            "Shows the action currently selected above."
        )
        main_layout.addWidget(self.selected_action_label)

        options_frame = QFrame()
        options_frame.setFrameShape(QFrame.StyledPanel)
        options_layout = QVBoxLayout()
        options_layout.setContentsMargins(12, 12, 12, 12)
        options_layout.setSpacing(12)
        options_frame.setLayout(options_layout)

        options_title = QLabel("Options")
        options_title_font = options_title.font()
        options_title_font.setBold(True)
        options_title.setFont(options_title_font)
        options_title.setToolTip(
            "These options change depending on the selected action."
        )
        options_layout.addWidget(options_title)

        self.options_stack = QStackedWidget()
        self.options_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.options_stack.setToolTip(
            "Settings relevant to the currently selected action."
        )

        self.rename_page = self._build_rename_page()
        self.organize_page = self._build_organize_page()
        self.rename_and_organize_page = self._build_rename_and_organize_page()
        self.undo_page = self._build_undo_page()

        self.options_stack.addWidget(self.rename_page)
        self.options_stack.addWidget(self.organize_page)
        self.options_stack.addWidget(self.rename_and_organize_page)
        self.options_stack.addWidget(self.undo_page)

        options_layout.addWidget(self.options_stack)
        main_layout.addWidget(options_frame)

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.preview_button = QPushButton("Preview")
        self.preview_button.setToolTip(
            "Create a preview of planned operations before files are changed."
        )
        self.preview_button.clicked.connect(self._handle_preview)
        button_row.addWidget(self.preview_button)

        main_layout.addStretch()
        main_layout.addLayout(button_row)

    def _build_rename_page(self) -> QWidget:
        """Create options page for rename action."""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        page.setLayout(layout)

        rename_format_label = QLabel("Rename format")
        rename_format_font = rename_format_label.font()
        rename_format_font.setBold(True)
        rename_format_label.setFont(rename_format_font)
        rename_format_label.setToolTip(
            "Choose how files should be renamed."
        )
        layout.addWidget(rename_format_label)

        self.rename_only_format_combo = QComboBox()
        self.rename_only_format_combo.addItem(
            "Date (YYYYMMDD_001)",
            "rename_by_date",
        )
        self.rename_only_format_combo.addItem(
            "Date and time (YYYYMMDD_HHMMSS_001)",
            "rename_by_datetime",
        )
        self.rename_only_format_combo.addItem(
            "Short date (YYMMDD_001)",
            "rename_by_short_date",
        )
        self.rename_only_format_combo.addItem(
            "Source and date (source_YYYYMMDD_001)",
            "rename_by_source_date",
        )
        self.rename_only_format_combo.currentIndexChanged.connect(
            self._update_rename_only_format_help
        )
        layout.addWidget(self.rename_only_format_combo)

        self.rename_help_label = QLabel("")
        self.rename_help_label.setWordWrap(True)
        layout.addWidget(self.rename_help_label)

        layout.addStretch()
        return page

    def _build_organize_page(self) -> QWidget:
        """Create options page for organize action."""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        page.setLayout(layout)

        folder_structure_label = QLabel("Folder structure")
        folder_structure_font = folder_structure_label.font()
        folder_structure_font.setBold(True)
        folder_structure_label.setFont(folder_structure_font)
        folder_structure_label.setToolTip(
            "Choose how destination folders should be created."
        )
        layout.addWidget(folder_structure_label)

        self.organize_only_structure_combo = QComboBox()
        self.organize_only_structure_combo.addItem("YEAR", "year")
        self.organize_only_structure_combo.addItem("YEAR / MONTH", "year_month")
        self.organize_only_structure_combo.addItem("YEAR / MONTH / DAY", "year_month_day")
        self.organize_only_structure_combo.setToolTip(
            "YEAR creates folders like 2024. YEAR / MONTH creates folders like 2024/03."
        )
        layout.addWidget(self.organize_only_structure_combo)

        operation_label = QLabel("File operation")
        operation_font = operation_label.font()
        operation_font.setBold(True)
        operation_label.setFont(operation_font)
        operation_label.setToolTip(
            "Choose whether files should be moved or copied."
        )
        layout.addWidget(operation_label)

        self.organize_only_operation_group = QButtonGroup(self)

        self.organize_only_move_radio = QRadioButton("Move files")
        self.organize_only_move_radio.setToolTip(
            "Move files to the target folders. Original files will no longer stay in the source folder."
        )

        self.organize_only_copy_radio = QRadioButton("Copy files")
        self.organize_only_copy_radio.setToolTip(
            "Copy files to the target folders and keep the original files unchanged."
        )

        self.organize_only_operation_group.addButton(self.organize_only_move_radio)
        self.organize_only_operation_group.addButton(self.organize_only_copy_radio)
        self.organize_only_move_radio.setChecked(True)

        layout.addWidget(self.organize_only_move_radio)
        layout.addWidget(self.organize_only_copy_radio)

        organize_help_label = QLabel(
            "Organize actions can move or copy files into date-based folders."
        )
        organize_help_label.setWordWrap(True)
        organize_help_label.setToolTip(
            "Copy is safer because it keeps the original files untouched."
        )
        layout.addWidget(organize_help_label)

        layout.addStretch()
        return page

    def _build_rename_and_organize_page(self) -> QWidget:
        """Create options page for rename and organize action."""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        page.setLayout(layout)

        folder_structure_label = QLabel("Folder structure")
        folder_structure_font = folder_structure_label.font()
        folder_structure_font.setBold(True)
        folder_structure_label.setFont(folder_structure_font)
        folder_structure_label.setToolTip(
            "Choose how destination folders should be created."
        )
        layout.addWidget(folder_structure_label)

        self.combined_structure_combo = QComboBox()
        self.combined_structure_combo.addItem("YEAR", "year")
        self.combined_structure_combo.addItem("YEAR / MONTH", "year_month")
        self.combined_structure_combo.addItem("YEAR / MONTH / DAY", "year_month_day")
        self.combined_structure_combo.setToolTip(
            "YEAR creates folders like 2024. YEAR / MONTH / DAY creates folders like 2024/03/15."
        )
        layout.addWidget(self.combined_structure_combo)

        operation_label = QLabel("File operation")
        operation_font = operation_label.font()
        operation_font.setBold(True)
        operation_label.setFont(operation_font)
        operation_label.setToolTip(
            "Choose whether files should be moved or copied."
        )
        layout.addWidget(operation_label)

        self.combined_operation_group = QButtonGroup(self)

        self.combined_move_radio = QRadioButton("Move files")
        self.combined_move_radio.setToolTip(
            "Move files to the target folders. Original files will no longer stay in the source folder."
        )

        self.combined_copy_radio = QRadioButton("Copy files")
        self.combined_copy_radio.setToolTip(
            "Copy files to the target folders and keep the original files unchanged."
        )

        self.combined_operation_group.addButton(self.combined_move_radio)
        self.combined_operation_group.addButton(self.combined_copy_radio)
        self.combined_move_radio.setChecked(True)

        layout.addWidget(self.combined_move_radio)
        layout.addWidget(self.combined_copy_radio)

        rename_format_label = QLabel("Rename format")
        rename_format_font = rename_format_label.font()
        rename_format_font.setBold(True)
        rename_format_label.setFont(rename_format_font)
        rename_format_label.setToolTip(
            "Choose how files should be renamed before being placed into folders."
        )
        layout.addWidget(rename_format_label)

        self.combined_format_combo = QComboBox()
        self.combined_format_combo.addItem(
            "Date (YYYYMMDD_001)",
            "rename_by_date",
        )
        self.combined_format_combo.addItem(
            "Date and time (YYYYMMDD_HHMMSS_001)",
            "rename_by_datetime",
        )
        self.combined_format_combo.addItem(
            "Short date (YYMMDD_001)",
            "rename_by_short_date",
        )
        self.combined_format_combo.addItem(
            "Source and date (source_YYYYMMDD_001)",
            "rename_by_source_date",
        )
        self.combined_format_combo.currentIndexChanged.connect(
            self._update_combined_format_help
        )
        layout.addWidget(self.combined_format_combo)

        self.combined_help_label = QLabel("")
        self.combined_help_label.setWordWrap(True)
        layout.addWidget(self.combined_help_label)

        layout.addStretch()
        return page

    def _build_undo_page(self) -> QWidget:
        """Create options page for undo action."""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        page.setLayout(layout)

        undo_title = QLabel("Undo")
        undo_title_font = undo_title.font()
        undo_title_font.setBold(True)
        undo_title.setFont(undo_title_font)
        undo_title.setToolTip(
            "Undo restores the last supported operation."
        )
        layout.addWidget(undo_title)

        undo_info = QLabel(
            "This action restores the last rename or move operation."
        )
        undo_info.setWordWrap(True)
        undo_info.setToolTip(
            "Undo is available for rename and move operations."
        )
        layout.addWidget(undo_info)

        undo_help = QLabel(
            "Copy operations are not affected."
        )
        undo_help.setWordWrap(True)
        undo_help.setToolTip(
            "Copy mode keeps original files unchanged, so undo is not needed."
        )
        layout.addWidget(undo_help)

        layout.addStretch()
        return page

    def _set_options_stack_stable_height(self) -> None:
        """Keep options area height stable when switching action."""
        pages = [
            self.rename_page,
            self.organize_page,
            self.rename_and_organize_page,
            self.undo_page,
        ]
        max_height = max(page.sizeHint().height() for page in pages)
        self.options_stack.setMinimumHeight(max_height)

    def _build_format_tooltip_text(self, naming_mode: str) -> str:
        """Return tooltip text for a naming format."""
        if naming_mode == "rename_by_date":
            return (
                "Rename files using the full date and daily sequence number.\n\n"
                "Example:\n"
                "20240321_001.jpg"
            )

        if naming_mode == "rename_by_datetime":
            return (
                "Rename files using date, time, and daily sequence number.\n\n"
                "Example:\n"
                "20240321_153045_001.jpg"
            )

        if naming_mode == "rename_by_short_date":
            return (
                "Rename files using the short date and daily sequence number.\n\n"
                "Example:\n"
                "240321_001.jpg"
            )

        if naming_mode == "rename_by_source_date":
            return (
                "Rename files using detected source and date.\n\n"
                "Examples:\n"
                "whatsapp_20240321_001.jpg\n"
                "signal_20260314_001.jpg\n"
                "messenger_20240321_001.jpg\n"
                "screenshot_20240321_001.png\n"
                "iphone_20240321_001.jpg\n"
                "photo_20240321_001.jpg"
            )

        return "Choose how files should be renamed."

    def _build_format_help_text(self, naming_mode: str) -> str:
        """Return help label text for a naming format."""
        if naming_mode == "rename_by_source_date":
            return (
                "The application tries to detect the source of files "
                "(WhatsApp, Signal, Messenger, screenshot, camera maker).\n"
                'If detection fails, files will use the "photo" prefix.'
            )

        return "Files will be renamed using the selected naming format."

    def _update_rename_only_format_help(self) -> None:
        """Update tooltip and help text for rename-only format combo."""
        naming_mode = self.rename_only_format_combo.currentData()
        tooltip_text = self._build_format_tooltip_text(naming_mode)
        help_text = self._build_format_help_text(naming_mode)
        self.rename_only_format_combo.setToolTip(tooltip_text)
        self.rename_help_label.setText(help_text)
        self.rename_help_label.setToolTip(tooltip_text)

    def _update_combined_format_help(self) -> None:
        """Update tooltip and help text for combined format combo."""
        naming_mode = self.combined_format_combo.currentData()
        tooltip_text = self._build_format_tooltip_text(naming_mode)
        help_text = self._build_format_help_text(naming_mode)
        self.combined_format_combo.setToolTip(tooltip_text)
        self.combined_help_label.setText(help_text)
        self.combined_help_label.setToolTip(tooltip_text)

    def _choose_folder(self) -> None:
        """Open folder selection dialog and store the selected path."""
        selected_folder = QFileDialog.getExistingDirectory(self, "Select input folder")

        if selected_folder:
            self.path_input.setText(selected_folder)

    def _get_selected_action_key(self) -> str:
        """Return internal action key based on selected radio button."""
        if self.rename_radio.isChecked():
            return "rename_photos"
        if self.organize_radio.isChecked():
            return "organize_photos"
        if self.rename_and_organize_radio.isChecked():
            return "rename_and_organize"
        if self.undo_radio.isChecked():
            return "undo"
        return ""

    def _get_selected_action_text(self) -> str:
        """Return user-facing label for the currently selected action."""
        action_map = {
            "rename_photos": "Rename photos",
            "organize_photos": "Organize photos",
            "rename_and_organize": "Rename and organize",
            "undo": "Undo",
        }
        return action_map.get(self._get_selected_action_key(), "")

    def _get_selected_sort_mode(self) -> str:
        """Return selected folder structure value for current action."""
        action_key = self._get_selected_action_key()

        if action_key == "organize_photos":
            return self.organize_only_structure_combo.currentData()

        if action_key == "rename_and_organize":
            return self.combined_structure_combo.currentData()

        return "year"

    def _get_selected_operation_mode(self) -> str:
        """Return selected file operation mode for current action."""
        action_key = self._get_selected_action_key()

        if action_key == "organize_photos":
            if self.organize_only_copy_radio.isChecked():
                return "copy"
            return "move"

        if action_key == "rename_and_organize":
            if self.combined_copy_radio.isChecked():
                return "copy"
            return "move"

        return "move"

    def _get_selected_naming_mode(self) -> str:
        """Return selected naming mode for current action."""
        action_key = self._get_selected_action_key()

        if action_key == "rename_photos":
            return self.rename_only_format_combo.currentData()

        if action_key == "rename_and_organize":
            return self.combined_format_combo.currentData()

        return "rename_by_date"

    def _on_action_changed(self) -> None:
        """Handle UI updates after action selection changes."""
        self._update_selected_action_label()
        self._update_options_page()
        self._update_primary_button_text()

    def _update_selected_action_label(self) -> None:
        """Refresh text showing which action is currently selected."""
        action_text = self._get_selected_action_text()
        self.selected_action_label.setText(f"Selected action: {action_text}")

    def _update_options_page(self) -> None:
        """Switch options page based on selected action."""
        action_key = self._get_selected_action_key()

        if action_key == "rename_photos":
            self.options_stack.setCurrentWidget(self.rename_page)
        elif action_key == "organize_photos":
            self.options_stack.setCurrentWidget(self.organize_page)
        elif action_key == "rename_and_organize":
            self.options_stack.setCurrentWidget(self.rename_and_organize_page)
        else:
            self.options_stack.setCurrentWidget(self.undo_page)

    def _update_primary_button_text(self) -> None:
        """Update primary button label based on selected action."""
        if self._get_selected_action_key() == "undo":
            self.preview_button.setText("Undo")
            self.preview_button.setToolTip(
                "Restore the last supported operation."
            )
        else:
            self.preview_button.setText("Preview")
            self.preview_button.setToolTip(
                "Create a preview of planned operations before files are changed."
            )

    def _validate_input_folder(self) -> bool:
        """Validate that the input folder exists when required."""
        if self._get_selected_action_key() == "undo":
            return True

        folder_text = self.path_input.text().strip()

        if not folder_text:
            QMessageBox.warning(self, "Missing folder", "Please select an input folder.")
            return False

        folder_path = Path(folder_text)

        if not folder_path.exists():
            QMessageBox.warning(self, "Folder not found", "The selected folder does not exist.")
            return False

        if not folder_path.is_dir():
            QMessageBox.warning(self, "Invalid folder", "The selected path is not a folder.")
            return False

        return True

    def _build_plan_from_gui(self):
        """Create RenamePlan from current GUI selections."""
        from core.planner import plan_operations
        from core.scanner import scan_folder
        from core.sorter import SORT_BY_DAY, SORT_BY_MONTH, SORT_BY_YEAR

        folder_path = self.path_input.text().strip()
        action_key = self._get_selected_action_key()

        if action_key == "undo":
            raise ValueError("Undo does not use preview plan.")

        photos, scan_errors, ignored_files, file_type_counts, total_files = scan_folder(folder_path)

        if not photos:
            return None

        sort_map = {
            "year": SORT_BY_YEAR,
            "year_month": SORT_BY_MONTH,
            "year_month_day": SORT_BY_DAY,
        }

        sort_mode = sort_map.get(self._get_selected_sort_mode(), SORT_BY_YEAR)

        if action_key == "rename_photos":
            operation_mode = "rename"
            naming_mode = self._get_selected_naming_mode()
        elif action_key == "organize_photos":
            operation_mode = self._get_selected_operation_mode()
            naming_mode = "keep_original_name"
        elif action_key == "rename_and_organize":
            operation_mode = self._get_selected_operation_mode()
            naming_mode = self._get_selected_naming_mode()
        else:
            raise ValueError(f"Unsupported action: {action_key}")

        rename_plan = plan_operations(
            photos,
            folder_path,
            scan_errors,
            ignored_files,
            total_files,
            sort_mode,
            operation_mode,
            naming_mode,
        )
        return rename_plan

    def _handle_preview(self) -> None:
        """Build preview plan or trigger undo flow."""
        if not self._validate_input_folder():
            return

        folder_path = self.path_input.text().strip()
        action_key = self._get_selected_action_key()

        if action_key == "undo":
            self.undo_requested.emit()
            return

        try:
            rename_plan = self._build_plan_from_gui()

            if rename_plan is None:
                QMessageBox.information(
                    self,
                    "No files",
                    "No supported media files were found in the selected folder.",
                )
                return

            self.preview_requested.emit(rename_plan, folder_path)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Preview error",
                f"An error occurred during preview:\n\n{error}",
            )