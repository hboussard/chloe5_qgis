import threading

from subprocess import Popen

from qgis.PyQt.QtCore import QObject, QThread, pyqtSignal

from ...helpers.helpers import CustomFeedback, kill_process_tree, run_command


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
        self._lock = threading.Lock()
        self._process: Popen | None = None
        self._canceled: bool = False

    def run(self) -> None:
        ran_successfully: bool = False
        try:
            ran_successfully = run_command(
                command_line=self._command_line,
                feedback=self._feedback,
                on_process_started=self._on_process_started,
            )
        except IOError:
            ran_successfully = False
        finally:
            with self._lock:
                self._process = None
            self.finished.emit(ran_successfully)

    def _on_process_started(self, process: Popen) -> None:
        """Called on the worker thread once the process is live."""
        with self._lock:
            self._process = process
            cancel_requested = self._canceled
        # Honor a cancel that arrived before the process had started.
        if cancel_requested:
            kill_process_tree(process)

    def cancel(self) -> None:
        """
        Kill the running process tree directly.

        Called from the GUI thread, so it does not depend on the worker's
        blocking stdout read reaching the cooperative ``isCanceled()`` check.
        """
        with self._lock:
            self._canceled = True
            process = self._process
        if process is not None:
            kill_process_tree(process)


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
        # Set the cooperative flag (so run_command bails out cleanly)...
        if self._signal_feedback is not None:
            self._signal_feedback.set_canceled(True)
        # ...and kill the process tree immediately, without waiting for the
        # worker's blocking stdout read to notice the flag.
        if self._worker is not None:
            self._worker.cancel()

    def _on_worker_finished(self, ok: bool) -> None:
        if self._signal_feedback is not None:
            self._signal_feedback.set_canceled(False)

        self._thread = None
        self._worker = None
        self._signal_feedback = None
        self.finished.emit(ok)
