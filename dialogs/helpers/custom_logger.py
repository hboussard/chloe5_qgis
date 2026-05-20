from qgis.PyQt.QtWidgets import QPlainTextEdit, QProgressBar

from enum import Enum, auto


class LogType(Enum):
    ERROR = auto()
    INFO = auto()
    SUCCESS = auto()
    COMMAND = auto()


class CustomLogger:
    def __init__(
        self, logging_widget: QPlainTextEdit, progress_bar: QProgressBar = None
    ) -> None:

        self._logging_widget = logging_widget
        self._progress_bar = progress_bar

        self._progress_bar_regexp: str = ""
        self._logging_widget_regexp: str = ""

        self._output_lines_list: list[str] = []

        self.command_canceled: bool = False

    def set_is_canceled(self, is_canceled: bool) -> None:
        self.command_canceled = is_canceled

    def line_style(self, input_message: str, log_type: LogType) -> str:

        color: str = "black"

        if log_type is LogType.ERROR:
            color = "red"
        elif log_type is LogType.SUCCESS:
            color = "green"
        elif log_type is LogType.COMMAND:
            color = "blue"

        return f'<span style="color:{color}">{input_message}</span><br/>'

    def append_to_log(self, log_line: str) -> None:
        self._output_lines_list.append(log_line)

    def clear_log(self) -> None:
        self._output_lines_list.clear()

    def get_log(self) -> list[str]:
        return self._output_lines_list

    def pushInfo(self, message: str) -> None:
        self._output_lines_list.append(message)
        self._logging_widget.insertHtml(self.line_style(message, LogType.INFO))

    def pushCommandInfo(self, message: str) -> None:
        self._output_lines_list.append(message)
        self._logging_widget.insertHtml(self.line_style(message, LogType.INFO))

    def pushConsoleInfo(self, message: str) -> None:
        self._output_lines_list.append(message)
        self._logging_widget.insertHtml(self.line_style(message, LogType.INFO))

    def setProgress(self, progress: float) -> None:
        self._progress_bar.setValue(int(progress))

    def isCanceled(self) -> bool:
        return self.command_canceled
