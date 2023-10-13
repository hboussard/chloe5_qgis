from processing.gui.wrappers import WidgetWrapper
from .factor_table_panel import FactorTablePanel
from .dataclasses import CombineFactorElement


class ChloeFactorTableWidgetWrapper(WidgetWrapper):
    def createWidget(self, input_matrix_param_name: str, parentWidgetConfig=None):
        """Widget creation to put like panel in dialog"""
        self.parentWidgetConfig = parentWidgetConfig
        return FactorTablePanel(
            parent=self.dialog,
            input_matrix_parameter_name=input_matrix_param_name,
            dialog_type=self.dialogType,
        )

    def setValue(self, value: "list[list[CombineFactorElement | list[str]] | str]"):
        """Set value on the widget/component.
        list[list[CombineFactorElement] | str] input value type is constrained by the modeler xml file's data passed to the widget.
        usefull option types in the model3 xml file are: List, QString (no tuples, dict or other complex objects allowed)
        """

        if value is None:
            return
        self.widget.setValue(value)

    def value(self):
        """Get value on the widget/component."""
        return self.widget.value()

    def getParentWidgetConfig(self):
        return self.parentWidgetConfig

    def refresh_factor_table(self):
        self.widget.populate_table_model()
