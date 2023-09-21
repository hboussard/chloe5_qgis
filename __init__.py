"""
/***************************************************************************
 Chloe 5
                                 A QGIS plugin
 TODO : Plugin description
                             -------------------
        begin                : 2023-09-21
        copyright            : (C) 2023 by Chloecompagny
        email                : Chloecompagny@Chloecompagny.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


def classFactory(iface):
    # load plugin class from file
    from .chloe_plugin import ChloePlugin

    return ChloePlugin(iface)
