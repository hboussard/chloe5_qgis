from processing.gui.wrappers import (
    WidgetWrapper,
)

from .double_list_selector_panel import DoubleListSelectionPanel


class ChloeDoubleListSelectorWidgetWrapper(WidgetWrapper):
    def createWidget(
        self,
        default_selected_metric: str,
        input_raster_layer_param_name: str,
        parent_widget_config=None,
    ):
        """Widget creation to put like panel in dialog"""
        self.parent_widget_config = parent_widget_config

        widget = DoubleListSelectionPanel(
            parent=self.dialog,
            dialog_type=self.dialogType,
            default_selected_metric=default_selected_metric,
            input_raster_layer_param_name=input_raster_layer_param_name,
        )

        return widget

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        self.widget.setValue(str(value))

    def value(self):
        """Get value on the widget/component."""
        return self.widget.getValue()

    def get_parent_widget_config(self):
        return self.parent_widget_config

    def refresh_metrics_combobox(self):
        self.widget.set_metrics()
        self.widget.populate_filter_combobox()
