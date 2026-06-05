from qgis.PyQt.QtCore import QObject, QThread, pyqtSignal

from ...helpers.helpers import CustomFeedback, run_command


class SignalFeedback(QObject):
    """Forwards run_command callbacks to Qt signals (delivered on the GUI thread)."""

    info = pyqtSignal(str)
    command = pyqtSignal(str)
    console = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(float)

    def __init__(self) -> None:
        super().__init__()
        self._canceled: bool = False

    def set_canceled(self, canceled: bool) -> None:
        self._canceled = canceled

    def pushInfo(self, message: str) -> None:
        self.info.emit(message)

    def pushCommandInfo(self, message: str) -> None:
        self.command.emit(message)

    def pushConsoleInfo(self, message: str) -> None:
        self.console.emit(message)

    def reportError(self, message: str) -> None:
        self.error.emit(message)

    def setProgress(self, progress: float) -> None:
        self.progress.emit(progress)

    def isCanceled(self) -> bool:
        return self._canceled


class CommandWorker(QObject):
    finished = pyqtSignal(bool)

    def __init__(self, command_line: str, feedback: SignalFeedback) -> None:
        super().__init__()
        self._command_line = command_line
        self._feedback = feedback

    def run(self) -> None:
        ran_successfully: bool = False
        try:
            ran_successfully = run_command(
                command_line=self._command_line, feedback=self._feedback
            )
        except IOError:
            ran_successfully = False
        finally:
            self.finished.emit(ran_successfully)


class BackgroundCommandExecutor(QObject):
    """
    Runs Chloe shell commands on a worker thread.

    Usage:
        self._executor = BackgroundCommandExecutor(self)
        self._executor.finished.connect(self._on_command_finished)
        self._executor.start(command_line, feedback_sink=self._logger)
        self._executor.cancel()  # Interrupt button
    """

    finished = pyqtSignal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: CommandWorker | None = None
        self._signal_feedback: SignalFeedback | None = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def start(self, command_line: str, feedback_sink: CustomFeedback) -> bool:
        """Start command on a background thread. Returns False if already running."""
        if self.is_running():
            return False

        self._signal_feedback = SignalFeedback()
        self._signal_feedback.set_canceled(False)
        # wire feedback signal to the feedback sink
        self._signal_feedback.info.connect(feedback_sink.pushInfo)
        self._signal_feedback.command.connect(feedback_sink.pushCommandInfo)
        self._signal_feedback.console.connect(feedback_sink.pushConsoleInfo)
        self._signal_feedback.error.connect(feedback_sink.reportError)
        self._signal_feedback.progress.connect(feedback_sink.setProgress)

        self._worker = CommandWorker(command_line, self._signal_feedback)
        self._thread = QThread(self.parent() or self)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()
        return True

    def cancel(self) -> None:
        if self._signal_feedback is not None:
            self._signal_feedback.set_canceled(True)

    def _on_worker_finished(self, ok: bool) -> None:
        if self._signal_feedback is not None:
            self._signal_feedback.set_canceled(False)

        self._thread = None
        self._worker = None
        self._signal_feedback = None
        self.finished.emit(ok)
