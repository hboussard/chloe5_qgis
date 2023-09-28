from processing.gui.wrappers import (
    FileWidgetWrapper,
    EnumWidgetWrapper,
)


class ChloeEnumUpdateStateWidgetWrapper(EnumWidgetWrapper):
    """A widget wrapper for a custom enum selection widget."""

    def createWidget(self, dependantWidgetConfig=None):
        """ """
        self.dependantWidgetConfig = dependantWidgetConfig
        return super().createWidget()

    def postInitialize(self, widgetWrapperList):
        self.widget.currentIndexChanged.connect(
            lambda x: self.updateDependantWidget(widgetWrapperList)
        )
        self.updateDependantWidget(widgetWrapperList)

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
