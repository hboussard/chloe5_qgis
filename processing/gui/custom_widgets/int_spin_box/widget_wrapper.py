from processing.gui.wrappers import (
    WidgetWrapper,
)

from .odd_even_number_spinbox import OddEvenIntSpinbox


class ChloeOddEvenIntSpinboxWrapper(WidgetWrapper):
    def createWidget(
        self,
        initial_value: int,
        min_value: int,
        max_value: int,
        odd_mode: bool,
    ):
        """Widget creation to put like panel in dialog"""

        spinbox: OddEvenIntSpinbox = OddEvenIntSpinbox(
            parent=self.dialog, odd_mode=odd_mode
        )
        spinbox.setMinimum(min_value)
        spinbox.setMaximum(max_value)
        spinbox.setValue(initial_value)

        return spinbox

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        self.widget.setValue(int(value))

    def value(self):
        """Get value on the widget/component."""
        return self.widget.getValue()
