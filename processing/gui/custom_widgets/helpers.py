from typing import Union
from processing.gui.wrappers import WidgetWrapper


def get_widget_wrapper_from_param_name(
    wrappers, param_name: str
) -> Union[WidgetWrapper, None]:
    """Returns the WidgetWrapper object from a list of wrappers that matches the given parameter name.

    Args:
        wrappers (list): A list of WidgetWrapper objects.
        param_name (str): The name of the parameter to match.

    Returns:
        WidgetWrapper: The WidgetWrapper object that matches the given parameter name.
    """
    for wrapper in wrappers:
        if wrapper.parameterDefinition().name() == param_name:
            return wrapper
    return None
