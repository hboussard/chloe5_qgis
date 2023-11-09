from pathlib import Path
from processing.gui.wrappers import (
    WidgetWrapper,
    DIALOG_MODELER,
    DIALOG_BATCH,
    DIALOG_STANDARD,
)
from .input_mapping_table_panel import TableMappingPanel
from qgis.PyQt.QtWidgets import (
    QLineEdit,
)
from ....algorithms.helpers.constants import MAP_CSV


class ChloeMappingTableWidgetWrapper(WidgetWrapper):
    def createWidget(self, input_raster_layer_param_name: str, parentWidgetConfig=None):
        """Widget creation to put like panel in dialog"""
        self.parentWidgetConfig = parentWidgetConfig

        if self.dialogType == DIALOG_MODELER:
            widget = QLineEdit()
            widget.setPlaceholderText("(1,3);(2,9)")
            if self.parameterDefinition().defaultValue():
                widget.setText(self.parameterDefinition().defaultValue())
            return widget
        else:
            return TableMappingPanel(
                parent=self.dialog,
                dialog_type=self.dialogType,
                input_raster_layer_param_name=input_raster_layer_param_name,
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

    def getParentWidgetConfig(self):
        return self.parentWidgetConfig

    def populate_csv_mapping_combobox(self):
        """Populate the widget csv mapping combobox using the csv file selected in param."""
        self.widget.populate_csv_header_combobox()

    def clear_mapping_table(self):
        """Clear the widget mapping table."""
        self.widget.clear_mapping_table()
