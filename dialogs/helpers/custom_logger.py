import datetime
import html

from enum import Enum, auto

from qgis.PyQt.QtWidgets import QTextEdit, QProgressBar


class LogType(Enum):
    ERROR = auto()
    INFO = auto()
    SUCCESS = auto()
    COMMAND = auto()
    CONSOLE = auto()


def format_message(message: str, escape_html: bool = True) -> str:
    return html.escape(message) if escape_html else message


class CustomLogger:
    def __init__(
        self, logging_widget: QTextEdit, progress_bar: QProgressBar | None = None
    ) -> None:
        self._logging_widget = logging_widget
        self._progress_bar = progress_bar
        self._output_lines_list: list[str] = []
        self.command_canceled: bool = False

    def set_is_canceled(self, is_canceled: bool) -> None:
        self.command_canceled = is_canceled

    def begin_execution(self, algorithm_name: str) -> None:
        """Log header lines like the Processing algorithm dialog."""
        started_at = datetime.datetime.now().replace(microsecond=0).isoformat()
        self.pushInfo(f"Algorithme commencé à : {started_at}")
        self.pushFormattedMessage(
            f"<b>Démarrage de l'algorithme « {html.escape(algorithm_name)} »…</b>"
        )
        self.pushInfo("")

    def line_style(self, input_message: str, log_type: LogType) -> str:
        color = "black"
        if log_type is LogType.ERROR:
            color = "red"
        elif log_type is LogType.SUCCESS:
            color = "green"
        elif log_type is LogType.COMMAND:
            color = "blue"
        elif log_type is LogType.CONSOLE:
            color = "grey"

        formatted = format_message(input_message)
        return f'<span style="color:{color}">{formatted}</span>'

    def append_to_log(self, log_line: str, log_type: LogType) -> None:
        self._logging_widget.append(self.line_style(log_line, log_type))
        self._output_lines_list.append(log_line)

    def clear_log(self) -> None:
        self._output_lines_list.clear()
        self._logging_widget.clear()
        self.command_canceled = False
        self.setProgress(0)

    def get_log(self) -> list[str]:
        return self._output_lines_list

    def pushFormattedMessage(self, html_message: str) -> None:
        self._output_lines_list.append(html_message)
        self._logging_widget.append(f"<span>{html_message}</span>")

    def pushInfo(self, message: str) -> None:
        if not message:
            return
        self._output_lines_list.append(message)
        self._logging_widget.append(self.line_style(message, LogType.INFO))

    def pushCommandInfo(self, message: str) -> None:
        self._output_lines_list.append(message)
        self._logging_widget.append(self.line_style(message, LogType.COMMAND))

    def pushConsoleInfo(self, message: str) -> None:
        self._output_lines_list.append(message)
        self._logging_widget.append(self.line_style(message, LogType.CONSOLE))

    def reportError(self, message: str) -> None:
        if not message:
            return
        self._output_lines_list.append(message)
        formatted = format_message(message)
        self._logging_widget.append(f'<span style="color:red">{formatted}</span>')

    def pushSuccess(self, message: str) -> None:
        if not message:
            return
        self._output_lines_list.append(message)
        self._logging_widget.append(self.line_style(message, LogType.SUCCESS))

    def setProgress(self, progress: float) -> None:
        if self._progress_bar is not None:
            self._progress_bar.setValue(int(progress))

    def isCanceled(self) -> bool:
        return self.command_canceled
