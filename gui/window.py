from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import QMainWindow, QMessageBox, QScrollArea, QStackedWidget

from core.renamer import undo_operations
from gui.pages.preview_page import PreviewPage
from gui.pages.setup_page import SetupPage
from gui.workers.execute_worker import ExecuteWorker

from PySide6.QtGui import QIcon
from core.resource_path import resource_path
from core.version import get_version

class MainWindow(QMainWindow):
    """Main window that switches between setup page and preview page."""

    def __init__(self) -> None:
        super().__init__()
        version = get_version()
        self.setWindowTitle(f"SortMyPhotos {version}")
        self.setWindowIcon(QIcon(resource_path("assets/app_icon.ico")))
        self.resize(900, 785)
        self.setMinimumSize(900, 700)

        base_dir = Path(__file__).resolve().parent.parent
        self.log_file_path = str(base_dir / "rename_log.txt")
        self.backup_file_path = str(base_dir / "rename_backup.json")

        self.execute_thread = None
        self.execute_worker = None

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.setup_page = SetupPage()

        self.setup_scroll = QScrollArea()
        self.setup_scroll.setWidgetResizable(True)
        self.setup_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setup_scroll.setWidget(self.setup_page)

        self.preview_page = PreviewPage()

        self.stack.addWidget(self.setup_scroll)
        self.stack.addWidget(self.preview_page)

        self.setup_page.preview_requested.connect(self._show_preview_page)
        self.setup_page.undo_requested.connect(self._handle_undo_request)
        self.preview_page.back_requested.connect(self._show_setup_page)
        self.preview_page.execute_requested.connect(self._start_execute_worker)
        self.preview_page.execution_finished.connect(self._handle_execution_finished)

        self._show_setup_page()

    def _show_setup_page(self) -> None:
        """Switch to the setup page."""
        self.stack.setCurrentWidget(self.setup_scroll)
        self.statusBar().showMessage("Ready")

    def _show_preview_page(self, rename_plan, folder_path: str) -> None:
        """Load preview data and switch to preview page."""
        self.preview_page.load_rename_plan(
            rename_plan,
            folder_path,
            self.log_file_path,
            self.backup_file_path,
        )
        self.stack.setCurrentWidget(self.preview_page)

        if rename_plan.conflicts:
            self.statusBar().showMessage(
                f"Preview loaded with {len(rename_plan.conflicts)} conflict(s)"
            )
        else:
            self.statusBar().showMessage(
                f"Preview loaded: {len(rename_plan.operations)} operations"
            )

    def _start_execute_worker(
        self,
        rename_plan,
        folder_path: str,
        log_file_path: str,
        backup_file_path: str,
    ) -> None:
        """Start background worker for execute operations."""
        if self.execute_thread is not None:
            return

        self.execute_thread = QThread()
        self.execute_worker = ExecuteWorker(
            rename_plan,
            folder_path,
            log_file_path,
            backup_file_path,
        )
        self.execute_worker.moveToThread(self.execute_thread)

        self.execute_thread.started.connect(self.execute_worker.run)
        self.execute_worker.progress_changed.connect(
            self.preview_page.update_execution_progress
        )
        self.execute_worker.finished.connect(self._handle_worker_finished)
        self.execute_worker.error.connect(self._handle_worker_error)

        self.execute_worker.finished.connect(self.execute_thread.quit)
        self.execute_worker.error.connect(self.execute_thread.quit)
        self.execute_thread.finished.connect(self._cleanup_execute_worker)

        self.execute_thread.start()
        self.statusBar().showMessage("Executing file operations...")

    def _handle_worker_finished(self) -> None:
        """Handle successful worker completion."""
        self.statusBar().showMessage("Execution completed successfully")
        self.preview_page.finish_execution_success()

    def _handle_worker_error(self, error_message: str) -> None:
        """Handle worker execution error."""
        self.statusBar().showMessage("Execution failed")
        self.preview_page.finish_execution_error(error_message)

    def _cleanup_execute_worker(self) -> None:
        """Clean up execute worker and thread after completion."""
        if self.execute_worker is not None:
            self.execute_worker.deleteLater()
            self.execute_worker = None

        if self.execute_thread is not None:
            self.execute_thread.deleteLater()
            self.execute_thread = None

    def _handle_execution_finished(self, summary_text: str) -> None:
        """Handle successful execution and return to setup page."""
        self._show_setup_page()
        self.statusBar().showMessage("Execution completed successfully")

    def _build_user_friendly_undo_error(self, error: Exception) -> str:
        """Convert technical undo error into a user-friendly message."""
        error_text = str(error)
        lower_text = error_text.lower()

        if isinstance(error, FileNotFoundError):
            return (
                "The backup file was not found.\n\n"
                "Undo cannot continue because there is no saved operation to restore."
            )

        if "older or invalid format" in lower_text:
            return (
                "The backup file format is not supported.\n\n"
                "It may have been created by an older version of the application."
            )

        if "does not contain base_folder" in lower_text:
            return (
                "The backup file is incomplete.\n\n"
                "Undo cannot continue safely because important information is missing."
            )

        if "does not contain operations" in lower_text:
            return (
                "The backup file is incomplete.\n\n"
                "Undo cannot continue safely because the operation list is missing."
            )

        if "invalid operations format" in lower_text:
            return (
                "The backup file is damaged or was modified manually.\n\n"
                "Undo cannot continue safely."
            )

        if "missing required fields" in lower_text:
            return (
                "The backup file is incomplete or was modified manually.\n\n"
                "Undo cannot continue safely."
            )

        if "non-absolute" in lower_text:
            return (
                "The backup file contains invalid file paths.\n\n"
                "Undo cannot continue safely."
            )

        if "outside base_folder" in lower_text:
            return (
                "The backup file contains inconsistent folder data.\n\n"
                "Undo cannot continue safely."
            )

        if "invalid for rename mode" in lower_text:
            return (
                "The backup file contains inconsistent rename data.\n\n"
                "Undo cannot continue safely."
            )

        if "unsupported operation_mode" in lower_text:
            return (
                "The backup file contains an unsupported operation type.\n\n"
                "Undo cannot continue safely."
            )

        return (
            "Undo could not be completed safely.\n\n"
            f"Technical details:\n{error_text}"
        )

    def _build_undo_not_performed_message(self) -> str:
        """Return a more user-friendly message for safe undo stop."""
        return (
            "Undo was not performed.\n\n"
            "Possible reasons:\n"
            "- the backup file is empty\n"
            "- the last operation used copy mode\n"
            "- files were already restored\n"
            "- undo detected a problem and stopped safely"
        )

    def _handle_undo_request(self) -> None:
        """Handle undo flow from setup page."""
        confirmation = QMessageBox.question(
            self,
            "Confirm undo",
            (
                "Do you really want to restore the last operation?\n\n"
                "The original base folder will be loaded automatically "
                "from the backup file."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirmation != QMessageBox.Yes:
            return

        try:
            undo_success = undo_operations(self.backup_file_path)

            if undo_success:
                QMessageBox.information(
                    self,
                    "Undo completed",
                    "The last operation was restored successfully.",
                )
                self.statusBar().showMessage("Undo completed successfully")
            else:
                QMessageBox.information(
                    self,
                    "Undo not performed",
                    self._build_undo_not_performed_message(),
                )
                self.statusBar().showMessage("Undo was not performed")

        except Exception as error:
            friendly_message = self._build_user_friendly_undo_error(error)
            QMessageBox.critical(
                self,
                "Undo failed",
                friendly_message,
            )
            self.statusBar().showMessage("Undo failed")