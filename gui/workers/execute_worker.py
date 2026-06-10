from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from core.renamer import execute_operations


class ExecuteWorker(QObject):
    """Worker that executes file operations in a background thread."""

    progress_changed = Signal(int, int, str)
    finished = Signal()
    error = Signal(str)

    def __init__(
        self,
        rename_plan,
        folder_path: str,
        log_file_path: str,
        backup_file_path: str,
    ) -> None:
        super().__init__()
        self.rename_plan = rename_plan
        self.folder_path = folder_path
        self.log_file_path = log_file_path
        self.backup_file_path = backup_file_path

    def _progress_callback(self, current: int, total: int, message: str) -> None:
        """Forward progress updates from core code to Qt signals."""
        self.progress_changed.emit(current, total, message)

    @Slot()
    def run(self) -> None:
        """Run execute_operations in a worker thread."""
        try:
            execute_operations(
                self.rename_plan,
                self.folder_path,
                self.log_file_path,
                self.backup_file_path,
                progress_callback=self._progress_callback,
            )
            self.finished.emit()
        except Exception as error:
            self.error.emit(str(error))