# -*- coding: utf-8 -*-

from processing.gui.AlgorithmDialog import AlgorithmDialog
from processing.gui.AlgorithmDialogBase import AlgorithmDialogBase
from processing.gui.ParametersPanel import ParametersPanel
from processing.gui.MultipleInputPanel import MultipleInputPanel
from processing.gui.NumberInputPanel import NumberInputPanel
from processing.gui.FileSelectionPanel import FileSelectionPanel
from qgis.gui import (
    QgsProjectionSelectionWidget,
    QgsProcessingLayerOutputDestinationWidget,
    QgsFileWidget,
)
from processing.tools.dataobjects import createContext

from processing.gui.wrappers import (
    WidgetWrapper,
    RasterWidgetWrapper,
)

from qgis.core import (
    QgsProcessingFeedback,
    QgsProcessingParameterDefinition,
    QgsProcessingException,
    QgsMessageLog,
    Qgis,
)

from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPlainTextEdit,
    QLineEdit,
    QComboBox,
    QCheckBox,
)

from ...helpers.helpers import get_console_command


class ChloeAlgorithmDialog(AlgorithmDialog):
    """ChloeAlgorithmDialog class. this dialog is shown to the user when opening a CHLOE 5 algorithm."""

    def __init__(self, alg, parent=None):
        super().__init__(alg, parent=parent)
        self.mainWidget().parametersHaveChanged()

    def getParametersPanel(self, alg, parent):
        return ChloeParametersPanel(parent, alg)


class ChloeParametersPanel(ParametersPanel):
    """ChloeParametersPanel class. this panel is shown to the user when opening a CHLOE 5 algorithm."""

    def __init__(self, parent, alg):
        super().__init__(parent, alg)

        self.dialog = parent

        w = QWidget()
        layout = QVBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(6)
        label = QLabel()
        label.setText(self.tr("Chloe Command line"))
        layout.addWidget(label)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)
        w.setLayout(layout)
        self.addExtraWidget(w)

        # self.pbHeader = pb
        self.connectParameterSignals()
        self.parametersHaveChanged()

    def initWidgets(self):
        super().initWidgets()

        for k in self.wrappers:
            w = self.wrappers[k]
            if hasattr(w, "getParentWidgetConfig"):
                config = w.getParentWidgetConfig()
                # print(config)
                if config is not None:
                    linked_params = config.get("linkedParams", [])
                    for linked_param in linked_params:
                        p = self.wrappers[linked_param["paramName"]]
                        m = getattr(w, linked_param["refreshMethod"])
                        if m is not None:
                            widget = (
                                p.widget
                                if issubclass(p.__class__, WidgetWrapper)
                                else p.wrappedWidget()
                            )
                            # add here widget signal connections

                            if isinstance(widget, FileSelectionPanel):
                                widget.leText.textChanged.connect(m)
                            elif isinstance(widget, QgsFileWidget):
                                widget.fileChanged.connect(m)
                            elif isinstance(p, RasterWidgetWrapper):
                                p.combo.valueChanged.connect(m)
                            elif isinstance(p, MultipleInputPanel):
                                p.selectionChanged.connect(m)
                                try:
                                    widget.selectionChanged.connect(m)
                                except Exception as error:
                                    QgsMessageLog.logMessage(
                                        f"an error occured cant get selectionChanged : {error} ",
                                        level=Qgis.Critical,
                                    )
                        else:
                            continue

    def connectParameterSignals(self):
        for wrapper in list(self.wrappers.values()):
            wrapper.widgetValueHasChanged.connect(self.parametersHaveChanged)

            # TODO - remove when all wrappers correctly emit widgetValueHasChanged!

            # For compatibility with 3.x API, we need to check whether the wrapper is
            # the deprecated WidgetWrapper class. If not, it's the newer
            # QgsAbstractProcessingParameterWidgetWrapper class
            # TODO QGIS 4.0 - remove
            if issubclass(wrapper.__class__, WidgetWrapper):
                w = wrapper.widget
            else:
                w = wrapper.wrappedWidget()

            self.connectWidgetChangedSignals(w)
            for c in w.findChildren(QWidget):
                self.connectWidgetChangedSignals(c)

    def connectWidgetChangedSignals(self, w):
        if isinstance(w, QLineEdit):
            w.textChanged.connect(self.parametersHaveChanged)
        elif isinstance(w, QComboBox):
            w.currentIndexChanged.connect(self.parametersHaveChanged)
        elif isinstance(w, QgsProjectionSelectionWidget):
            w.crsChanged.connect(self.parametersHaveChanged)
        elif isinstance(w, QCheckBox):
            w.stateChanged.connect(self.parametersHaveChanged)
        elif isinstance(w, MultipleInputPanel):
            w.selectionChanged.connect(self.parametersHaveChanged)
        elif isinstance(w, NumberInputPanel):
            w.hasChanged.connect(self.parametersHaveChanged)
        elif isinstance(w, QgsProcessingLayerOutputDestinationWidget):
            w.destinationChanged.connect(self.parametersHaveChanged)

    def parametersHaveChanged(self):
        context = createContext()
        feedback = QgsProcessingFeedback()

        try:
            # messy as all heck, but we don't want to call the dialog's implementation of
            # createProcessingParameters as we want to catch the exceptions raised by the
            # parameter panel instead...
            parameters = (
                {}
                if self.dialog.mainWidget() is None
                else self.dialog.mainWidget().createProcessingParameters()
            )
            for output in self.algorithm().destinationParameterDefinitions():
                if not output.name() in parameters or parameters[output.name()] is None:
                    if (
                        not output.flags()
                        & QgsProcessingParameterDefinition.FlagOptional
                    ):
                        parameters[output.name()] = self.tr("[temporary file]")
            for p in self.algorithm().parameterDefinitions():
                if p.flags() & QgsProcessingParameterDefinition.FlagHidden:
                    continue

                if (
                    p.flags() & QgsProcessingParameterDefinition.FlagOptional
                    and p.name() not in parameters
                ):
                    continue

                if p.name() not in parameters or not p.checkValueIsAcceptable(
                    parameters[p.name()]
                ):
                    # not ready yet
                    self.text.setPlainText("")
                    return

            try:
                command: str = get_console_command(
                    self.algorithm().get_properties_file_path(parameters)
                )
                self.text.setPlainText(command)
            except QgsProcessingException as e:
                self.text.setPlainText(str(e))
        except AlgorithmDialogBase.InvalidParameterValue as e:
            self.text.setPlainText(
                self.tr("Invalid value for parameter '{0}'").format(
                    e.parameter.description()
                )
            )
        except AlgorithmDialogBase.InvalidOutputExtension as e:
            self.text.setPlainText(e.message)
