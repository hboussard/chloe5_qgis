from processing.gui.wrappers import WidgetWrapper
from .classification_table_panel import ClassificationTablePanel


class ChloeClassificationTableWidgetWrapper(WidgetWrapper):
    def createWidget(self, input_raster_param_name: str, parent_widget_config=None):
        """Widget creation to put like panel in dialog"""
        self.parent_widget_config = parent_widget_config
        return ClassificationTablePanel(
            parent=self.dialog,
            input_raster_param_name=input_raster_param_name,
            dialog_type=self.dialogType,
        )

    def get_parent_widget_config(self):
        return self.parent_widget_config

    def check_domains(self):
        self.widget.check_domains()

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        self.widget.setValue(value)

    def value(self):
        """Get value on the widget/component."""
        return self.widget.value()
