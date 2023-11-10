# -*- coding: utf-8 -*-

"""
*********************************************************************************************
    odd_even_number_spinbox.py
    ---------------------
        A spinbox of odd or even numbers 
        
        Date                 : June 2019

        email                : daan.guillerme at fdc22.com / hugues.boussard at inra.fr
*********************************************************************************************

"""

from qgis.PyQt.QtWidgets import QSpinBox


class OddEvenIntSpinbox(QSpinBox):

    """Integer Spinbox with odd or even numbers"""

    def __init__(self, parent, odd_mode: bool = False):
        super().__init__(parent)
        self.dialog = parent
        # specifies wether spinbox value should be odd (True) or even (False)
        self.is_odd_mode: bool = odd_mode
        self.setSingleStep(2)

    def get_next_odd_or_even_value(self, value):
        """
        Returns the next odd or even value based on the current value and the odd_mode value.

        If odd_mode is True, this method returns the next odd value if the current value is even,
        and the current value if it's odd. If odd_mode is False, this method returns the next even
        value if the current value is odd, and the current value if it's even.

        Args:
            value (int): The current value of the spinbox.

        Returns:
            int: The next odd or even value based on the current value and the odd_mode.
        """
        if (self.is_odd_mode and value % 2 == 0) or (
            self.is_odd_mode is False and value % 2 > 0
        ):
            return value + 1
        else:
            return value

    def update_value(self):
        self.setValue(self.get_next_odd_or_even_value(self.value()))

    def focusOutEvent(self, event):
        self.update_value()
        super().focusOutEvent(event)

    def getValue(self):
        return self.value()
