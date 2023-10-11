from processing.gui.wrappers import WidgetWrapper, DIALOG_MODELER
from qgis.PyQt.QtWidgets import QLineEdit
from .values_selection_panel import ValuesSelectionPanel

from ....algorithms.helpers.constants import INPUT_RASTER


class ChloeValuesWidgetWrapper(WidgetWrapper):
    def createWidget(self, input_raster=INPUT_RASTER):
        """Widget creation to put like panel in dialog"""
        # STANDARD GUI
        if self.dialogType == DIALOG_MODELER:
            widget = QLineEdit()  # QgsPanelWidget()
            return widget
        else:
            return ValuesSelectionPanel(
                parent=self.dialog,
                dialog_type=self.dialogType,
                input_raster_param_name=input_raster,
            )

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        if self.dialogType == DIALOG_MODELER:
            self.widget.setText(str(value))
        else:
            self.widget.setValue(str(value))

    def value(self):
        """Get value on the widget/component."""
        if self.dialogType == DIALOG_MODELER:
            return self.widget.text()
        else:
            return self.widget.getValue()
