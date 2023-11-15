from functools import partial
from typing import Any, Union
from processing.gui.wrappers import (
    FileWidgetWrapper,
    BooleanWidgetWrapper,
    EnumWidgetWrapper,
)

from processing.gui.wrappers import (
    WidgetWrapper,
    DIALOG_STANDARD,
)

from ..helpers import get_widget_wrapper_from_param_name


class ChloeCheckboxUpdateStateWidgetWrapper(BooleanWidgetWrapper):
    """A widget wrapper for a custom enum selection widget."""

    def createWidget(self, enabled_widgets_configs: list[dict[str, Any]] = []):
        """ """
        # self.enabled_widgets_configs = enabled_widgets_configs
        self.enabled_widgets_configs: list[dict[str, Any]] = enabled_widgets_configs
        return super().createWidget()

    def postInitialize(self, wrappers):
        if self.dialogType == DIALOG_STANDARD:
            self.widget.stateChanged.connect(
                partial(self.update_enabled_widgets, wrappers)
            )
        else:
            self.widget.currentIndexChanged.connect(
                partial(self.update_enabled_widgets, wrappers)
            )

    def update_enabled_widgets(self, wrappers):
        """
        Updates the enabled state of the enabled_widgets_configs widgets based on the current value of the checkbox.

        """
        for enabled_widget_config in self.enabled_widgets_configs:
            # Find the wrapper for the parameter that will be impacted
            wrapper: Union[WidgetWrapper, None] = get_widget_wrapper_from_param_name(
                wrappers, enabled_widget_config["param_name"]
            )
            if not wrapper:
                continue
            if isinstance(wrapper, (FileWidgetWrapper, EnumWidgetWrapper)):
                widget = wrapper.widget
            else:
                widget = wrapper.wrappedWidget()

            widget.setEnabled(self.value() == enabled_widget_config["enabled_by_value"])
