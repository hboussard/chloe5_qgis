# -*- coding: utf-8 -*-
"""
/***************************************************************************
 chloe plugin
                                Chloe 5 plugin
 

                              -------------------
        begin                : 2023-09-21
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Fédération des Chasseurs des Côtes d'Armor
        email                : daan.guillerme@fdc22.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from typing import Union
from qgis.gui import QgsMessageBar
from qgis.core import QgsApplication, QgsProcessingProvider
from .processing.chloe_algorithm_provider import ChloeAlgorithmProvider


class ChloePlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor."""
        self.iface = iface
        self.provider: Union[QgsProcessingProvider, None] = None

    def initGui(self):
        """Initialize the plugin GUI."""
        self.init_processing()

    def init_processing(self):
        """Initialize processing provider."""
        self.provider = ChloeAlgorithmProvider()
        if self.provider:
            QgsApplication.processingRegistry().addProvider(self.provider)
        else:
            self.iface.messageBar().pushMessage(
                "Chloe processing provider",
                "Chloe processing provider failed to load",
                level=QgsMessageBar.CRITICAL,
            )

    def unload(self):
        """Unload the plugin."""
        QgsApplication.processingRegistry().removeProvider(self.provider)
