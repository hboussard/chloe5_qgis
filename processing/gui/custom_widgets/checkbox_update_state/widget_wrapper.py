from processing.gui.wrappers import (
    FileWidgetWrapper,
    BooleanWidgetWrapper,
    EnumWidgetWrapper,
)


class ChloeCheckboxUpdateStateWidgetWrapper(BooleanWidgetWrapper):
    """A widget wrapper for a custom enum selection widget."""

    def createWidget(self, dependantWidgetConfig=None):
        """ """
        self.dependantWidgetConfig = dependantWidgetConfig
        return super().createWidget()

    def postInitialize(self, widgetWrapperList):
        self.widget.stateChanged.connect(
            lambda x: self.updateDependantWidget(widgetWrapperList)
        )
        self.updateDependantWidget(widgetWrapperList)

    def updateDependantWidget(self, wrapperList):
        if self.dependantWidgetConfig:
            for c in self.dependantWidgetConfig:
                param_name: str = c["paramName"]
                enable_value = c["enableValue"]

                dependant_wrapper_list = [
                    wrapper
                    for wrapper in wrapperList
                    if wrapper.parameterDefinition().name() == param_name
                ]

                if dependant_wrapper_list:
                    dependant_wrapper = dependant_wrapper_list[0]
                    dependant_widget = (
                        dependant_wrapper.widget
                        if isinstance(
                            dependant_wrapper, (FileWidgetWrapper, EnumWidgetWrapper)
                        )
                        else dependant_wrapper.wrappedWidget()
                    )

                    dependant_widget.setEnabled(self.value() == enable_value)
