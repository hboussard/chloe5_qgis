# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.PyQt.QtWidgets import (
    QDialog,
    QListView,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel
from qgis.core import QgsMessageLog, Qgis


class DialListCheckBox(QDialog):
    """
    Dialog with list check box
    example : 1,2,4,6,8
    """

    def __init__(self, values: list[int], checked_values: list[int] = []):
        super().__init__(parent=None)

        self.list_view_model: QStandardItemModel = QStandardItemModel()
        self.return_values: list[int] = []

        self.init_gui()

        self.populate_list_view_model(values, checked_values)

    def init_gui(self) -> None:
        """Init the GUI"""
        # Layout Principal
        main_layout: QVBoxLayout = QVBoxLayout(self)

        # List item checkable
        list_view: QListView = QListView()
        list_view.setModel(self.list_view_model)
        main_layout.addWidget(list_view)

        # Sub layout for buttons
        buttons_vertical_layout: QHBoxLayout = QHBoxLayout()
        main_layout.addLayout(buttons_vertical_layout)

        # List buttons
        btn_all = QPushButton(self.tr("All"))
        btn_nothing = QPushButton(self.tr("Nothing"))
        btn_submit = QPushButton(self.tr("Ok"))

        buttons_vertical_layout.addWidget(btn_all)
        buttons_vertical_layout.addWidget(btn_nothing)
        buttons_vertical_layout.addWidget(btn_submit)

        btn_all.clicked.connect(self.select_all_values)

        btn_nothing.clicked.connect(self.unselect_all_values)

        btn_submit.clicked.connect(self.submit)

    def populate_list_view_model(
        self, values: list[int], checked_values: list[int]
    ) -> None:
        """
        Populates the list view model based on a values list.

        Args:
            values (list[int]): The list of values to populate the model with.
            checked_values (list[int]): The list of values that should be checked in the model.

        Returns:
            None
        """
        for v in values:
            item: QStandardItem = QStandardItem(str(v))
            if v in checked_values:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            item.setCheckable(True)
            self.list_view_model.appendRow(item)

    def select_all_values(self):
        """select all values in the list view model"""
        self.set_listview_items_checked_state()

    def unselect_all_values(self):
        """Unselected all values in the list view model"""
        self.set_listview_items_checked_state(checked=False)

    def set_listview_items_checked_state(self, checked: bool = True):
        """Set the checked state of all items in the list view model"""
        for index in range(self.list_view_model.rowCount()):
            item = self.list_view_model.item(index)
            if item.isCheckable() and item.checkState() is not checked:
                item.setCheckState(checked)

    def submit(self):
        """Get value of checked items and exit"""
        # Iteration sur le model (contient la list des items)
        for index in range(self.list_view_model.rowCount()):
            item = self.list_view_model.item(index)
            if item.isCheckable() and item.checkState() == Qt.Checked:  # Si Checked
                try:
                    self.return_values.append(int(item.text()))
                except ValueError:
                    QgsMessageLog.logMessage(
                        self.tr(f"The value {item.text()} is not an integer"),
                        level=Qgis.Critical,
                    )
        self.close()

    def run(self):
        self.setWindowTitle(self.tr("Select values"))
        self.exec_()
        return self.return_values

    def tr(self, string, context=""):
        if context == "" or context == None:
            context = self.__class__.__name__
        return QCoreApplication.translate(context, string)
