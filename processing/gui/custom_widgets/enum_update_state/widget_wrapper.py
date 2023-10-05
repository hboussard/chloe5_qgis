from functools import partial
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


class ChloeEnumUpdateStateWidgetWrapper(EnumWidgetWrapper):
    """A widget wrapper for a custom enum selection widget."""

    def createWidget(self, fast_mode_options=[], dependantWidgetConfig=None):
        self.fast_mode_options = fast_mode_options
        # create a copy of the default options
        self.default_mode_options = self.parameterDefinition().options()
        self.dependantWidgetConfig = dependantWidgetConfig
        return super().createWidget()

    def postInitialize(self, widgetWrapperList):
        self.widget.currentIndexChanged.connect(
            lambda x: self.updateDependantWidget(widgetWrapperList)
        )
        self.updateDependantWidget(widgetWrapperList)

        # Find the wrapper for the 'FAST' parameter
        for wrapper in widgetWrapperList:
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

    def updateDependantWidget(self, wrapperList):
        if self.dependantWidgetConfig:
            for c in self.dependantWidgetConfig:
                dependantWrapperList = list(
                    filter(
                        lambda w: w.parameterDefinition().name() == c["paramName"],
                        wrapperList,
                    )
                )
                if len(dependantWrapperList) > 0:
                    dependantWrapper = dependantWrapperList[0]
                    if isinstance(dependantWrapper, FileWidgetWrapper):
                        dependantWidget = dependantWrapper.widget
                    else:
                        dependantWidget = dependantWrapper.wrappedWidget()
                    dependantWidget.setEnabled(self.value() == c["enableValue"])

    def refresh_widget_options(self):
        print(self.widget)
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
        is_fast_value: bool = fast_param_wrapper.parameterValue()
        if not self.fast_mode_options:
            return
        print(f"fast mode: {is_fast_value}")
        if is_fast_value:
            print(f"options: {self.fast_mode_options}")
            self.parameterDefinition().setOptions(self.fast_mode_options)
        else:
            self.parameterDefinition().setOptions(self.default_mode_options)

        self.refresh_widget_options()
