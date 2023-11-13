from functools import partial
from typing import Any, Union
from processing.gui.wrappers import (
    FileWidgetWrapper,
    EnumWidgetWrapper,
)
from processing.gui.wrappers import (
    WidgetWrapper,
    DIALOG_MODELER,
    DIALOG_BATCH,
    DIALOG_STANDARD,
)
from ....algorithms.helpers.constants import FAST
from ..helpers import get_widget_wrapper_from_param_name


class ChloeEnumUpdateStateWidgetWrapper(EnumWidgetWrapper):
    """A widget wrapper for a custom enum selection widget."""

    def createWidget(
        self,
        fast_mode_options: list[Any] = [],
        enabled_widgets_configs: list[dict[str, Any]] = [],
    ):
        self.fast_mode_options: list[Any] = fast_mode_options
        # create a copy of the default options
        self.default_mode_options: list[Any] = self.parameterDefinition().options()
        self.enabled_widgets_configs: list[dict[str, Any]] = enabled_widgets_configs

        return super().createWidget()

    def postInitialize(self, wrappers):
        self.widget.currentIndexChanged.connect(
            partial(self.update_enabled_widgets, wrappers)
        )
        self.update_enabled_widgets(wrappers)

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

    def update_enabled_widgets(self, wrappers):
        """Update the impacted widgets based on the current value of the widget"""

        # Find the wrapper for the 'FAST' parameter
        fast_mode_wrapper: Union[
            None, WidgetWrapper
        ] = get_widget_wrapper_from_param_name(wrappers, FAST)

        for enabled_widget_config in self.enabled_widgets_configs:
            # Find the wrapper for the parameter that will be impacted
            wrapper: Union[WidgetWrapper, None] = get_widget_wrapper_from_param_name(
                wrappers, enabled_widget_config["param_name"]
            )
            if not wrapper:
                continue
            # If the parameter enable state is controlled by the fast mode parameter
            if "disabled_by_fast_mode" in enabled_widget_config and fast_mode_wrapper:
                if (
                    enabled_widget_config["disabled_by_fast_mode"]
                    == fast_mode_wrapper.parameterValue()
                ):
                    wrapper.wrappedWidget().setEnabled(False)
                    continue
            if isinstance(wrapper, (FileWidgetWrapper, EnumWidgetWrapper)):
                widget = wrapper.widget
            else:
                widget = wrapper.wrappedWidget()
            widget.setEnabled(self.value() == enabled_widget_config["enabled_by_value"])

    def refresh_widget_options(self):
        self.widget.clear()
        for i, option in enumerate(self.parameterDefinition().options()):
            self.widget.addItem(option, i)
        # if self.dialogType in (DIALOG_STANDARD, DIALOG_BATCH):
        #     self._useCheckBoxes = useCheckBoxes
        #     if self._useCheckBoxes and not self.dialogType == DIALOG_BATCH:
        #         return CheckboxesPanel(
        #             options=self.parameterDefinition().options(),
        #             multiple=self.parameterDefinition().allowMultiple(),
        #             columns=columns,
        #         )
        #     if self.parameterDefinition().allowMultiple():
        #         return MultipleInputPanel(options=self.parameterDefinition().options())
        #     else:
        #         for i, option in enumerate(self.parameterDefinition().options()):
        #             widget.addItem(option, i)
        #     self.combobox.clear()
        #     for i, option in enumerate(self.parameterDefinition().options()):
        #         self.combobox.addItem(option, i)

    def set_fast_mode(self, fast_param_wrapper):
        """Set the fast mode of the widget based on the value of the fast mode parameter"""
        is_fast_value: bool = fast_param_wrapper.parameterValue()
        if not self.fast_mode_options:
            return
        if is_fast_value:
            self.parameterDefinition().setOptions(self.fast_mode_options)
        else:
            self.parameterDefinition().setOptions(self.default_mode_options)

        self.refresh_widget_options()
