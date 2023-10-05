import os
import signal
import platform
from typing import Protocol, Union
from re import search
from qgis.core import QgsMessageLog, Qgis, QgsProcessingFeedback
from .constants import CHLOE_WORKING_DIRECTORY_PATH


class CustomFeedback(Protocol):
    def pushInfo(self, message: str) -> None:
        ...

    def pushCommandInfo(self, message: str) -> None:
        ...

    def pushConsoleInfo(self, message: str) -> None:
        ...

    def setProgress(self, progress: float) -> None:
        ...

    def isCanceled(self) -> bool:
        ...


def run_command(
    command_line: str,
    feedback: Union[CustomFeedback, None] = None,
) -> None:
    """
    Runs a command line command and logs the output.

    Args:
        command_line (str): The command line command to run.
        feedback (Union[CustomFeedback, None], optional): The feedback object to use for logging. Defaults to None.
    """

    if feedback is None:
        feedback = QgsProcessingFeedback()

    QgsMessageLog.logMessage(command_line, "Processing", Qgis.Info)
    feedback.pushInfo("CHLOE command:")
    feedback.pushCommandInfo(command_line)
    feedback.pushInfo("CHLOE command output:")

    success = False
    retry_count = 0
    while not success:
        loglines = []
        loglines.append("CHLOE execution console output")
        try:
            with Popen(
                command_line,
                shell=True,
                stdout=PIPE,
                stdin=DEVNULL,
                stderr=STDOUT,
                # universal_newlines=True,
                cwd=str(CHLOE_WORKING_DIRECTORY_PATH),
            ) as process:
                success = True

                for byte_line in process.stdout:
                    if feedback.isCanceled():
                        if platform.system() == "Windows":
                            os.call(
                                [
                                    "taskkill",
                                    "/F",
                                    "/T",
                                    "/PID",
                                    str(process.pid),
                                ]
                            )
                        else:
                            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                        return
                    line = byte_line.decode("utf8", errors="backslashreplace").replace(
                        "\r", ""
                    )
                    feedback.pushConsoleInfo(line)
                    loglines.append(line)
                    # get progress value from line using regex
                    progress_value: float = get_progress_value_from_line(line)
                    feedback.setProgress(progress_value)

        except IOError as error:
            if retry_count < 5:
                # print('retry ' + str(retry_count))
                retry_count += 1
            else:
                raise IOError(
                    str(error)
                    + f'\nTried 5 times without success. Last iteration stopped after reading {len(loglines)} line(s).\nLast line(s):\n{",".join(loglines[-10:])}'
                ) from error

        QgsMessageLog.logMessage("\n".join(loglines), "Processing", Qgis.Info)


def get_progress_value_from_line(line: str) -> float:
    progress: float = 0.0

    re_percent = search("^#(100|\d{1,2})$", line)

    if re_percent:
        try:
            float(re_percent.group(1))
        except ValueError:
            QgsMessageLog.logMessage(
                f"Impossible de convertir en float le pourcentage de progression : {re_percent.group(1)}",
            )
    return progress
