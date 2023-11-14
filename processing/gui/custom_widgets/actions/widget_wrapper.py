from processing.gui.wrappers import (
    WidgetWrapper,
)


class ChloeActionWidgetWrapper(WidgetWrapper):
    """Base class for widgets that are not used as parameters but rather as actions (buttons, etc.)) in the algorithm dialog."""

    def setValue(self, value):
        """Set value on the widget/component. Since the widget is not used as a parameter, this method is not used."""
        pass

    def value(self):
        """Get value on the widget/component. Since the widget is not used as a parameter, this method returns an empty string."""
        return ""
