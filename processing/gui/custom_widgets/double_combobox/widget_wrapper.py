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
    def createLabel(self):
        """Label create"""
        if self.dialogType == DIALOG_STANDARD:
            return super().createLabel()
        else:
            return super().createLabel()

    def postInitialize(self, wrappers):
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
        default_selected_metric,
        input_raster_layer_param_name,
        parentWidgetConfig=None,
    ):
        """Widget creation to put like panel in dialog"""
        self.parentWidgetConfig = parentWidgetConfig

        return DoubleCmbBoxSelectionPanel(
            parent=self.dialog,
            dialog_type=self.dialogType,
            default_selected_metric=default_selected_metric,
            input_raster_layer_param_name=input_raster_layer_param_name,
        )

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        self.widget.setValue(str(value))

    def value(self):
        """Get value on the widget/component."""
        return self.widget.getValue()

    def getParentWidgetConfig(self):
        return self.parentWidgetConfig

    def refresh_metrics_combobox(self):
        self.widget.set_metrics()
        self.widget.populate_metric_filter_combobox()

    def set_fast_mode(self, fast_param_wrapper):
        is_fast_value: bool = fast_param_wrapper.parameterValue()
        self.widget.set_fast_mode(is_fast_value)
