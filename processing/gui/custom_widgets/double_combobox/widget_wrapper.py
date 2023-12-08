from functools import partial
from processing.gui.wrappers import (
    WidgetWrapper,
    DIALOG_MODELER,
    DIALOG_BATCH,
    DIALOG_STANDARD,
)
from .double_cmb_box_selection_panel import DoubleCmbBoxSelectionPanel
from ....algorithms.helpers.constants import FAST


class ChloeDoubleComboboxWidgetWrapper(WidgetWrapper):
    def postInitialize(self, wrappers):
        """Post initialization of the widget/component."""
        # Find the wrapper for the 'FAST' parameter
        for wrapper in wrappers:
            if wrapper.parameterDefinition().name() == FAST:
                # Connect to the `widgetValueHasChanged` signal of the 'FAST' wrapper
                if self.dialogType == DIALOG_STANDARD:
                    wrapper.widget.stateChanged.connect(
                        partial(self.set_fast_mode, wrapper)
                    )
                else:
                    wrapper.widget.currentIndexChanged.connect(
                        partial(self.set_fast_mode, wrapper)
                    )
                break

    def createWidget(
        self,
        default_selected_metric: str,
        input_raster_layer_param_name: str,
        parent_widget_config=None,
    ):
        """Widget creation to put like panel in dialog"""
        self.parent_widget_config = parent_widget_config

        widget = DoubleCmbBoxSelectionPanel(
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
        self.widget.populate_metric_filter_combobox()

    def set_fast_mode(self, fast_param_wrapper):
        is_fast_value: bool = fast_param_wrapper.parameterValue()
        self.widget.set_fast_mode(is_fast_value)
