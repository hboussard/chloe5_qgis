from typing import Union

from qgis.PyQt.QtGui import (
    QIntValidator,
    QRegExpValidator,
)
from qgis.PyQt.QtCore import Qt, QRegExp
from qgis.PyQt.QtWidgets import (
    QItemDelegate,
    QLineEdit,
    QMessageBox,
)

from .....helpers.helpers import tr
from .dataclasses import DomainValue, from_string_to_domain, DOMAIN_REGEX


class ClassificationModelIntValueDelegate(QItemDelegate):
    """
    A delegate for handling integer values in a QTableView.

    This delegate provides a QLineEdit editor with a QIntValidator to ensure that only integer values are entered.
    It also checks if the entered value already exists in the model but not in the same row, and displays an error message if it does.
    If the entered value is not a valid integer, it displays an error message as well.

    Args:
        parent (QObject): The parent object of the delegate.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.validator = QIntValidator(self)
        self.validator.setBottom(0)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(self.validator)
        return editor

    def setModelData(self, editor, model, index):
        value_str = editor.text()
        # check if the value already exists in the model but not in the same row
        try:
            value_int = int(value_str)
        except ValueError:
            QMessageBox.critical(
                None,
                tr("Invalid value"),
                f"{tr('Value')} {value_str} {tr('is not a valid integer')}",
            )
            return

        model.setData(index, value_int, Qt.EditRole)


class DomainValueDelegate(QItemDelegate):
    """
    A delegate for handling domain values in a QTableView.

    This delegate provides a QLineEdit editor with a QRegExpValidator to ensure that only valid domain values are entered.
    A domain value should follow the interval syntax. Examples: [0,1[ or ],-1] or [2,[.
    If the entered value is not a valid domain value, it displays an error message.

    Args:
        parent (QObject): The parent object of the delegate.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.regex = QRegExp(DOMAIN_REGEX)
        self.validator = QRegExpValidator(self.regex, self)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(self.validator)
        return editor

    def setModelData(self, editor, model, index):
        editor_value: str = editor.text()
        domain_value: Union[DomainValue, None] = from_string_to_domain(editor_value)
        if domain_value is not None:
            # check if the domain value overlaps with another domain value in the table
            overlapping_domains: list[DomainValue] = model.domains_overlaps(
                domain_to_check=domain_value, row_to_skip_index=index.row()
            )
            if overlapping_domains:
                QMessageBox.warning(
                    editor,
                    tr("Invalid domain value"),
                    f"{tr('The domain value')} {str(domain_value)} {tr('overlaps with the following domains in the table')} : {','.join([str(dom) for dom in overlapping_domains])}",
                )
                return
            model.setData(index, str(domain_value), Qt.EditRole)
