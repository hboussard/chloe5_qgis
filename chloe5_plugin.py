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
from pathlib import Path
from qgis.core import QgsApplication, QgsProcessingProvider, Qgis, QgsMessageLog
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtWidgets import QAction, QWidget, QMenu, QToolBar, QMenuBar
from qgis.PyQt.QtGui import QIcon
from .processing.chloe_algorithm_provider import ChloeAlgorithmProvider
from .settings.settings_dialog import SettingsDialog
from .dialogs.chloe_grain import ChloeGrainDialog


class Chloe5Plugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor."""
        self.iface = iface

        # Declare instance attributes
        self.actions: list[QAction] = []

        self.menu = QMenu(self.iface.mainWindow())
        self.menu_name: str = self.tr("Chloe5")

        # NO TOOLBAR YET
        # self.toolbar = self.iface.addToolBar("&Chloe")
        self.toolbar: QToolBar = None

        self.processing_provider: QgsProcessingProvider = ChloeAlgorithmProvider()
        self.plugin_settings_dialog: SettingsDialog = SettingsDialog()

    def initGui(self):
        """Initialize the plugin GUI."""
        self.init_translator()
        self.init_menu()
        self.init_toolbar()
        self.init_processing()

    def init_processing(self):
        """Initialize processing provider."""
        if self.processing_provider:
            QgsApplication.processingRegistry().addProvider(self.processing_provider)
        else:
            self.iface.messageBar().pushMessage(
                "Chloe processing provider",
                "Chloe processing provider failed to load",
                level=Qgis.Critical,
            )

    def init_menu(self):
        """Initialize the plugin menu."""

        self.menu.setObjectName(self.menu_name)
        self.menu.setTitle(self.menu_name)

        grainIcon_path = Path(__file__).resolve().parent / "images" / "chloe_icon.png"
        self.add_action(
            self.menu,
            QIcon(str(grainIcon_path)),
            text=self.tr("Chloé 5 : Grain"),
            callback=self.runGrain,
            parent=self.iface.mainWindow(),
        )
        # plugin settings separator
        separator = QAction()
        separator.setSeparator(True)
        self.menu.addSeparator()

        self.add_action(
            self.menu,
            QIcon(QgsApplication.iconPath("propertyicons/settings.svg")),
            text=self.tr("Configuration du plugin"),
            callback=self.open_settings_dialog,
            add_to_toolbar=False,
            parent=self.iface.mainWindow(),
        )
        self.first_start_grain = True

        qgis_menu_bar: QMenuBar = self.iface.mainWindow().menuBar()
        menu = qgis_menu_bar
        for child in qgis_menu_bar.children():
            if child.objectName() == "mPluginMenu":
                menu = child
                break
        menu.addMenu(self.menu)

    def init_toolbar(self):
        """Initialize the plugin toolbar."""
        pass

    def tr(self, message: str):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate("Chloe5Plugin", message)

    def init_translator(self):
        """Initialize locale."""
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path: Path = (
            Path(__file__).parent / "i18n" / f"Chloe5_{locale}_{locale.upper()}.qm"
        )
        self.translator = QTranslator()
        if locale_path.exists():
            self.translator.load(str(locale_path))
        else:
            # warning
            QgsMessageLog.logMessage(
                f"Could not load translation file {locale}", level=Qgis.Critical
            )

            self.iface.messageBar().pushMessage(
                "Chloe5Plugin",
                f"Could not load translation file {locale}",
                level=Qgis.Warning,
            )

        QCoreApplication.installTranslator(self.translator)

    def add_action(
        self,
        menu: QMenu,
        icon: QIcon,
        text: str,
        callback,
        enabled_flag: bool = True,
        add_to_menu: bool = True,
        add_to_toolbar: bool = True,
        status_tip: str = "",
        whats_this: str = "",
        parent: QWidget = None,
    ):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar and self.toolbar:
            # Adds plugin icon to Plugins toolbar
            self.toolbar.addAction(action)
        elif add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            menu.addAction(action)

        self.actions.append(action)

        return action

    def open_settings_dialog(self):
        """Open settings dialog."""
        self.plugin_settings_dialog.show()

    def unload(self):
        """Unload the plugin."""

        QgsApplication.processingRegistry().removeProvider(self.processing_provider)
        self.menu.deleteLater()
        for action in self.actions:
            self.iface.removePluginMenu(self.menu_name, action)
            self.iface.removeToolBarIcon(action)

    def runGrain(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start_grain == True:
            self.first_start_grain = False
            self.dlg_grain = ChloeGrainDialog()

        # show the dialog
        if not self.dlg_grain.isVisible():
            self.dlg_grain.show()
            # Run the dialog event loop
            result = self.dlg_grain.exec_()
            # See if OK was pressed
            if result:
                # Do something useful here - delete the line containing pass and
                # substitute with your code.
                self.dlg_grain.makePropertiesFile()
