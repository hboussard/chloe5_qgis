from processing.gui.wrappers import WidgetWrapper, DIALOG_MODELER
from qgis.PyQt.QtWidgets import QLineEdit
from ....algorithms.helpers.constants import INPUT_RASTER
from .values_selector_panel import ValuesSelectorPanel
from .selector_data_strategy import ValueSelectorStrategy, RasterValueSelectorStrategy


class ChloeValuesWidgetWrapper(WidgetWrapper):
    """Wrapper for the value selector panel"""

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


class ChloeRasterValuesWidgetWrapper(ChloeValuesWidgetWrapper):
    """Wrapper for the value selector panel based on a raster input"""

    def createWidget(self, input_raster=INPUT_RASTER):
        # STANDARD GUI
        if self.dialogType == DIALOG_MODELER:
            widget = QLineEdit()  # QgsPanelWidget()
            return widget
        else:
            selector_strategy: ValueSelectorStrategy = RasterValueSelectorStrategy(
                dialog_type=self.dialogType,
                input_raster_name=input_raster,
                algorithm_dialog=self.dialog,
            )
            return ValuesSelectorPanel(
                selector_strategy=selector_strategy, placeholder_text="1;2;3;4"
            )
