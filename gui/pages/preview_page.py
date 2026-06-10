from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class PreviewPage(QWidget):
    """Page showing preview table, summary and conflicts."""

    back_requested = Signal()
    execute_requested = Signal(object, str, str, str)
    execution_finished = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.current_rename_plan = None
        self.current_folder_path = ""
        self.log_file_path = ""
        self.backup_file_path = ""
        self.is_executing = False
        self._build_ui()

    def _build_ui(self) -> None:
        """Create and arrange widgets for the preview page."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)

        title_label = QLabel("Preview operations")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setToolTip(
            "This page shows all planned file operations before execution."
        )
        main_layout.addWidget(title_label)

        subtitle_label = QLabel("Review planned operations before execution.")
        subtitle_label.setWordWrap(True)
        subtitle_label.setToolTip(
            "Check file names, target folders, and status before you continue."
        )
        main_layout.addWidget(subtitle_label)

        preview_frame = QFrame()
        preview_frame.setFrameShape(QFrame.StyledPanel)

        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(12, 12, 12, 12)
        preview_layout.setSpacing(10)
        preview_frame.setLayout(preview_layout)

        table_title = QLabel("Planned operations")
        table_title_font = table_title.font()
        table_title_font.setBold(True)
        table_title.setFont(table_title_font)
        table_title.setToolTip(
            "Each row shows one planned rename, move, or copy operation."
        )
        preview_layout.addWidget(table_title)

        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(6)
        self.preview_table.setHorizontalHeaderLabels(
            [
                "Old name",
                "New name",
                "Date",
                "Date source",
                "Target folder",
                "Status",
            ]
        )
        self.preview_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.preview_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.setToolTip(
            "Preview of all planned operations. Status OK means the file will be processed. "
            "Status SKIP means no change is needed."
        )

        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.preview_table.setColumnWidth(4, 260)

        preview_layout.addWidget(self.preview_table, 1)

        summary_title = QLabel("Preview summary")
        summary_title_font = summary_title.font()
        summary_title_font.setBold(True)
        summary_title.setFont(summary_title_font)
        summary_title.setToolTip(
            "Summary of detected files, planned operations, skipped files, and errors."
        )
        preview_layout.addWidget(summary_title)

        self.summary_label = QLabel("No preview loaded.")
        self.summary_label.setWordWrap(True)
        self.summary_label.setToolTip(
            "Shows the main statistics for the current preview."
        )
        preview_layout.addWidget(self.summary_label)

        conflicts_title = QLabel("Conflicts")
        conflicts_title_font = conflicts_title.font()
        conflicts_title_font.setBold(True)
        conflicts_title.setFont(conflicts_title_font)
        conflicts_title.setToolTip(
            "If conflicts are listed here, execution will be blocked until they are resolved."
        )
        preview_layout.addWidget(conflicts_title)

        self.conflicts_label = QLabel("No conflicts.")
        self.conflicts_label.setWordWrap(True)
        self.conflicts_label.setToolTip(
            "Shows file name or path conflicts detected during preview."
        )
        preview_layout.addWidget(self.conflicts_label)

        self.progress_title_label = QLabel("Execution progress")
        progress_title_font = self.progress_title_label.font()
        progress_title_font.setBold(True)
        self.progress_title_label.setFont(progress_title_font)
        self.progress_title_label.setToolTip(
            "Shows progress while files are being processed."
        )
        preview_layout.addWidget(self.progress_title_label)

        self.progress_status_label = QLabel("")
        self.progress_status_label.setWordWrap(True)
        self.progress_status_label.setToolTip(
            "Shows the current file operation in progress."
        )
        preview_layout.addWidget(self.progress_status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setToolTip(
            "Progress of the current execute operation."
        )
        preview_layout.addWidget(self.progress_bar)

        main_layout.addWidget(preview_frame, 1)

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.back_button = QPushButton("Back")
        self.back_button.setToolTip(
            "Return to the setup page without changing any files."
        )
        self.back_button.clicked.connect(self.back_requested.emit)
        button_row.addWidget(self.back_button)

        self.execute_button = QPushButton("Execute")
        self.execute_button.setToolTip(
            "Run the planned operations shown in this preview."
        )
        self.execute_button.clicked.connect(self._handle_execute)
        button_row.addWidget(self.execute_button)

        main_layout.addLayout(button_row)

        self._reset_progress_ui()

    def _set_table_item(self, row: int, column: int, text: str) -> None:
        """Create and assign a non-editable table item."""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setToolTip(text)
        self.preview_table.setItem(row, column, item)

    def _fill_preview_table(self, rename_plan) -> None:
        """Fill preview table from RenamePlan operations."""
        self.preview_table.setRowCount(len(rename_plan.operations))

        for row, operation in enumerate(rename_plan.operations):
            target_folder_text = str(operation.target_folder)

            status_text = "SKIP" if operation.skipped else "OK"
            date_text = operation.photo_date.strftime("%Y-%m-%d %H:%M:%S")

            self._set_table_item(row, 0, operation.original_name)
            self._set_table_item(row, 1, operation.new_name)
            self._set_table_item(row, 2, date_text)
            self._set_table_item(row, 3, operation.date_source)
            self._set_table_item(row, 4, target_folder_text)
            self._set_table_item(row, 5, status_text)

        self.preview_table.scrollToTop()

    def _update_summary_labels(self, rename_plan) -> None:
        """Update summary and conflicts labels from RenamePlan."""
        stats = rename_plan.stats

        summary_text = (
            f"Files found: {stats.files_found} | "
            f"EXIF dates: {stats.exif_dates} | "
            f"File dates: {stats.file_dates} | "
            f"Planned operations: {stats.planned_operations} | "
            f"Skipped: {stats.skipped} | "
            f"Ignored files: {stats.ignored_files} | "
            f"Conflicts: {stats.conflicts} | "
            f"Errors: {stats.errors}"
        )
        self.summary_label.setText(summary_text)

        if rename_plan.conflicts:
            self.conflicts_label.setText("\n".join(rename_plan.conflicts))
        else:
            self.conflicts_label.setText("No conflicts.")

    def _set_execution_controls_enabled(self, enabled: bool) -> None:
        """Enable or disable page buttons during execution."""
        self.back_button.setEnabled(enabled)
        self.execute_button.setEnabled(enabled)

    def _reset_progress_ui(self) -> None:
        """Hide and reset execution progress widgets."""
        self.progress_title_label.setVisible(False)
        self.progress_status_label.setVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_status_label.setText("")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.is_executing = False
        self._set_execution_controls_enabled(True)

    def load_rename_plan(
        self,
        rename_plan,
        folder_path: str,
        log_file_path: str,
        backup_file_path: str,
    ) -> None:
        """Load RenamePlan data into preview page."""
        self.current_rename_plan = rename_plan
        self.current_folder_path = folder_path
        self.log_file_path = log_file_path
        self.backup_file_path = backup_file_path
        self._fill_preview_table(rename_plan)
        self._update_summary_labels(rename_plan)
        self._reset_progress_ui()

    def _build_completion_summary(self) -> str:
        """Build summary text after successful execution."""
        total_files = len(self.current_rename_plan.operations)
        skipped_files = sum(
            1 for operation in self.current_rename_plan.operations if operation.skipped
        )
        changed_files = total_files - skipped_files

        return (
            f"Operation completed successfully.\n\n"
            f"Processed files: {total_files}\n"
            f"Changed files: {changed_files}\n"
            f"Skipped files: {skipped_files}"
        )

    def _build_user_friendly_execution_error(self, error_message: str) -> str:
        """Convert technical execute error text into a user-friendly message."""
        lower_message = error_message.lower()

        if "temporary file already exists" in lower_message:
            return (
                "The operation could not continue because a temporary working file "
                "already exists in the selected folder.\n\n"
                "Try removing old temporary files and run the operation again."
            )

        if "permission" in lower_message:
            return (
                "The operation could not continue because the application does not "
                "have permission to access one or more files.\n\n"
                "Close any programs that may be using the files and try again."
            )

        if "file not found" in lower_message or "no such file" in lower_message:
            return (
                "The operation could not continue because one or more files were not found.\n\n"
                "The selected folder may have changed since preview was created. "
                "Please go back, create a new preview, and try again."
            )

        return (
            "The operation could not be completed.\n\n"
            "Please review the selected folder and try again.\n\n"
            f"Technical details:\n{error_message}"
        )

    def start_execution_ui(self) -> None:
        """Prepare progress UI before worker execution starts."""
        self.is_executing = True
        self._set_execution_controls_enabled(False)
        self.progress_title_label.setVisible(True)
        self.progress_status_label.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_status_label.setText("Preparing file operations...")

    def update_execution_progress(self, current: int, total: int, message: str) -> None:
        """Update progress widgets during execution."""
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
        else:
            self.progress_bar.setRange(0, 0)

        self.progress_status_label.setText(f"{message} ({current}/{total})")

    def finish_execution_success(self) -> None:
        """Show success message and emit completion signal."""
        self.is_executing = False
        self._set_execution_controls_enabled(True)

        if self.progress_bar.maximum() > 0:
            self.progress_bar.setValue(self.progress_bar.maximum())

        self.progress_status_label.setText("Execution completed successfully.")

        summary_text = self._build_completion_summary()

        QMessageBox.information(
            self,
            "Execution completed",
            summary_text,
        )

        self.execution_finished.emit(summary_text)

    def finish_execution_error(self, error_message: str) -> None:
        """Show execution error and keep user on preview page."""
        self.is_executing = False
        self._set_execution_controls_enabled(True)

        friendly_message = self._build_user_friendly_execution_error(error_message)

        QMessageBox.critical(
            self,
            "Execution failed",
            friendly_message,
        )

    def _handle_execute(self) -> None:
        """Validate execution and request background execution."""
        if self.current_rename_plan is None:
            QMessageBox.information(
                self,
                "Missing preview",
                "No preview data is loaded.",
            )
            return

        if self.current_rename_plan.conflicts:
            QMessageBox.warning(
                self,
                "Execution blocked",
                "Conflicts were detected. Execution is blocked until conflicts are resolved.",
            )
            return

        total_files = len(self.current_rename_plan.operations)
        skipped_files = sum(
            1 for operation in self.current_rename_plan.operations if operation.skipped
        )
        changed_files = total_files - skipped_files

        confirmation = QMessageBox.question(
            self,
            "Confirm execution",
            (
                f"Do you want to execute these operations?\n\n"
                f"Processed files: {total_files}\n"
                f"Files with changes: {changed_files}\n"
                f"Skipped files: {skipped_files}"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirmation != QMessageBox.Yes:
            return

        self.start_execution_ui()

        self.execute_requested.emit(
            self.current_rename_plan,
            self.current_folder_path,
            self.log_file_path,
            self.backup_file_path,
        )