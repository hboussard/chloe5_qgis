from processing.gui.wrappers import WidgetWrapper, DIALOG_STANDARD, DIALOG_BATCH
from qgis.PyQt.QtWidgets import QLineEdit
from .values_selection_panel import ValuesSelectionPanel

from ....algorithms.helpers.constants import INPUT_RASTER


class ChloeValuesWidgetWrapper(WidgetWrapper):
    def createLabel(self):
        """Label create"""
        if self.dialogType == DIALOG_STANDARD:
            return super().createLabel()
        else:
            return super().createLabel()

    def createWidget(self, input_raster=INPUT_RASTER):
        """Widget creation to put like panel in dialog"""
        # STANDARD GUI
        if self.dialogType == DIALOG_STANDARD:
            return ValuesSelectionPanel(
                self.dialog, self.param.algorithm(), None, input_raster
            )
        # BATCH GUI
        elif self.dialogType == DIALOG_BATCH:
            return ValuesSelectionPanel(
                self.dialog, self.param.algorithm(), None, input_raster, True
            )
        # MODELER GUI
        else:
            widget = QLineEdit()  # QgsPanelWidget()
            return widget

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        # STANDARD AND BATCH GUI
        if self.dialogType in (DIALOG_STANDARD, DIALOG_BATCH):
            self.widget.setValue(str(value))
        else:
            self.widget.setText(str(value))

    def value(self):
        """Get value on the widget/component."""
        # STANDARD AND BATCH GUI
        if self.dialogType in (DIALOG_STANDARD, DIALOG_BATCH):
            return self.widget.getValue()
        else:
            return self.widget.text()
