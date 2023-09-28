from .double_cmb_box_selection_panel import DoubleCmbBoxSelectionPanel
from processing.gui.wrappers import (
    WidgetWrapper,
    DIALOG_MODELER,
    DIALOG_BATCH,
    DIALOG_STANDARD,
)


class ChloeDoubleComboboxWidgetWrapper(WidgetWrapper):
    def createLabel(self):
        """Label create"""
        if self.dialogType == DIALOG_STANDARD:
            return super().createLabel()
        else:
            return super().createLabel()

    def createWidget(
        self, dictValues, initialValue, rasterLayerParamName, parentWidgetConfig=None
    ):
        """Widget creation to put like panel in dialog"""
        self.parentWidgetConfig = parentWidgetConfig
        # STANDARD GUI
        if self.dialogType == DIALOG_STANDARD:
            return DoubleCmbBoxSelectionPanel(
                self.dialog,
                self.param.algorithm(),
                dictValues,
                initialValue,
                rasterLayerParamName,
            )
        # BATCH GUI
        elif self.dialogType in (DIALOG_BATCH, DIALOG_MODELER):
            return DoubleCmbBoxSelectionPanel(
                self.dialog,
                self.param.algorithm(),
                dictValues,
                initialValue,
                rasterLayerParamName,
                False,
            )
            # get raster values
        # MODELER GUI
        # else:
        #     widget = QLineEdit()
        #     widget.setPlaceholderText("")
        #     if self.parameterDefinition().defaultValue():
        #         widget.setText(self.parameterDefinition().defaultValue())
        #     return widget

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        if self.dialogType == DIALOG_STANDARD:
            self.widget.setValue(str(value))
        else:
            self.widget.setValue(str(value))

    def value(self):
        """Get value on the widget/component."""
        if self.dialogType == DIALOG_STANDARD:
            return self.widget.getValue()
        else:
            return self.widget.getValue()

    def getParentWidgetConfig(self):
        return self.parentWidgetConfig

    def refreshMappingCombobox(self):
        self.widget.calculate_metrics()
        self.widget.update_metrics()
