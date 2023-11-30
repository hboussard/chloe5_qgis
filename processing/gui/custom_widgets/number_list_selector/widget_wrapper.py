from processing.gui.wrappers import WidgetWrapper

from .number_list_selector_panel import NumberListSelectionPanel


class ChloeIntListSelectorWidgetWrapper(WidgetWrapper):
    def createWidget(
        self,
        default_value: int,
        min_value: int,
        max_value: int,
        single_step_value: int = 1,
    ):
        """Widget creation to put like panel in dialog"""
        widget = NumberListSelectionPanel()
        widget.set_spinbox_minimum_value(min_value)
        widget.set_spinbox_maximum_value(max_value)
        widget.set_spinbox_value(default_value)
        widget.set_spinbox_steps(single_step_value)
        return widget

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        self.widget.setValue(str(value))

    def value(self):
        """Get value on the widget/component."""
        return self.widget.getValue()
