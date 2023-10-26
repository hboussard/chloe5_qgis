# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ChloeEcolandscapesDialog
                                 A QGIS plugin
 Ce plugin met en oeuvre les concepts d'Ecopaysages,  de grain bocager et de continuités écologiques
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-07-17
        git sha              : $Format:%H$
        copyright            : (C) 2023 by INRAE
        email                : contact.chloe@inrae.fr
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

import os,datetime
from typing import Union

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets,QtCore
from qgis.core import QgsMapLayerProxyModel
from qgis.PyQt.QtWidgets import QWidget,QVBoxLayout,QLabel,QHBoxLayout,QPushButton,QFileDialog,QDialogButtonBox
from qgis.PyQt.QtGui import QTextCursor
from qgis.gui import QgsMapLayerComboBox
from .helpers.helpers import InputLayerFileWidget,get_console_command

from ..helpers.helpers import run_command



# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
GRAIN_FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'chloe_grain_dialog.ui'))

class ChloeGrainDialog(QtWidgets.QDialog, GRAIN_FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(ChloeGrainDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.inputMNHClayerfile = InputLayerFileWidget()
        self.inputMNHClayerfile.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.groupBox_MNHC.layout().addWidget(self.inputMNHClayerfile,0,1)

        self.inputplantationslayerfile = InputLayerFileWidget()
        self.inputplantationslayerfile.setFilters(QgsMapLayerProxyModel.LineLayer|QgsMapLayerProxyModel.PolygonLayer)
        self.groupBox_plantations.layout().insertWidget(0,self.inputplantationslayerfile)
        self.inputplantationslayerfile.connectLayerChangedSlot(self.mFieldComboBox_hauteurVegetation.setLayer)

        self.inputarasementslayerfile = InputLayerFileWidget()
        self.inputarasementslayerfile.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.groupBox_arasements.layout().insertWidget(0,self.inputarasementslayerfile)

        self.cursor = QTextCursor(self.textEdit_journal.document())
        self.pushButton_interrupt.clicked.connect(self.interruptWork)

        self.pushButton_run = QPushButton("Run")
        self.button_box.addButton(self.pushButton_run,QDialogButtonBox.ActionRole)
        self.pushButton_run.clicked.connect(self.run_grain)

        #self.mMapLayerComboBox_Plantations.mMapLayer.setFilters(QgsMapLayerProxyModel.VectorLayer)
        #self.mMapLayerComboBox_Plantations.layerChanged.connect(self.mFieldComboBox_hauteurVegetation.setLayer)
    
    def create_properties_file(self) -> str:
        # récupérer dossier courant
        prop_file = self.mQgsFileWidget_resultDir.filePath() + '/chloe_grain_'+datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S.%f")+'.properties'

        # créer le fichier properties
        with open(prop_file, "w") as f:
            f.write('procedure=grain_bocager\n')

            # les variables de la boite de dialogue :
            # onglet (1)

            # onglet (2)
            self.doubleSpinBox_seuilFonctionnel.text()
            self.doubleSpinBox_seuilPotentiel.text()
            self.doubleSpinBox_seuilOuvert.text()
            self.spinBox_radius.text()
            self.doubleSpinBox_pixelSize.text()


            # Dossier de sortie
            dirPath = self.mQgsFileWidget_resultDir.filePath()
            prefix = self.lineEdit_resultPrefix.text()
            filepath = dirPath+'/'+prefix+'_'
            f.write('output_path="'+dirPath+'"'+'\n')
            f.write('name="'+prefix+'"'+'\n')

            extent = self.mExtentGroupBox.currentExtent()
            if extent.xMinimum()!=0. and extent.xMaximum()!=0. and extent.yMinimum()!=0. and extent.yMaximum()!=0.:
                f.write("enveloppe={"+str(extent.xMinimum())+";"+str(extent.xMaximum())+";"+str(extent.yMinimum())+";"+str(extent.yMaximum())+"}\n")

            # self.mExtentGroupBox.currentExtent()
            if not self.mQgsDoubleSpinBox_buffer.text().isspace():
                f.write( 'buffer_area='+str(self.mQgsDoubleSpinBox_buffer.value())+'\n')

            if self.radioButton_rasterMNHC.isChecked():
                f.write( 'bocage="'+self.inputMNHClayerfile.currentLayer().source()+'"' +'\n')
            else:
                f.write( 'bocage="'+self.mQgsFileWidget_dirMNHC.filePath()+'"' +'\n')

            # scénario (onglet 3)
            if self.groupBox_arasements.isChecked():
                f.write( 'suppression="'+self.inputarasementslayerfile.currentLayer().source()+'"' +'\n')
                        
            if self.groupBox_plantations.isChecked() :
                f.write( 'plantations="'+self.inputplantationslayerfile.currentLayer().source()+'"'+'\n')
                if self.radioButton_valeurHauteurVegetation.isChecked():
                    f.write( 'hauteur_plantations='+self.lineEdit_hauteurVegetation.text() +'\n')
                elif self.radioButton_champHauteurVegetation.isChecked():
                    f.write( 'attribut_hauteur_plantations='+self.mFieldComboBox_hauteurVegetation.currentField() +'\n')


            # sorties (onglet 4)
            treatment = ''
            
            if self.checkBox_hauteurBoisements.isChecked(): # recuperation_hauteur_boisement
                treatment = 'recuperation_hauteur_boisement'
                f.write( 'hauteur_boisement="' + filepath + 'hauteur_boisement.tif"'+'\n' )

            if self.checkBox_typesBoisements.isChecked(): # detection_type_boisement
                treatment = 'detection_type_boisement'
                f.write( 'type_boisement="' + filepath + 'type_boisement.tif"'+'\n' )

            if self.checkBox_distanceInfluence.isChecked(): # calcul_distance_influence_boisement
                treatment = 'calcul_distance_influence_boisement'
                f.write( 'distance_influence="' + filepath + 'distance_influence.tif"' +'\n')

            if self.checkBox_grain.isChecked(): # calcul_grain_bocager
                treatment = 'calcul_grain_bocager'
                f.write( 'grain_bocager="' + filepath + 'grain_bocager.tif"' +'\n')
            if self.checkBox_grain4classes.isChecked(): # calcul_grain_bocager
                treatment = 'calcul_grain_bocager'
                f.write( 'grain_bocager_4classes="' + filepath + 'grain_bocager_4classes.tif"'+'\n' )

            if self.checkBox_grainMask.isChecked(): # clusterisation_fonctionnalite
                treatment = 'clusterisation_fonctionnalite'
                f.write( 'grain_bocager_fonctionnel="' + filepath + 'grain_bocager_fonctionnel.tif"' +'\n')
            if self.checkBox_clusters.isChecked(): # clusterisation_fonctionnalite
                treatment = 'clusterisation_fonctionnalite'
                f.write( 'clusterisation_grain_bocager_fonctionnel="' + filepath + 'clusters.tif"'+'\n' ) 

            if self.checkBox_enjeux.isChecked(): # calcul_enjeux_globaux
                treatment = 'calcul_enjeux_globaux'
                f.write( 'enjeux_window_radius="'+self.lineEdit_radiusEnjeux.text()+'"\n' )
                f.write( 'proportion_grain_bocager_fonctionnel="' + filepath + 'proportion_grain_fonctionnel.tif'+'"\n' )
                f.write( 'fragmentation_grain_bocager_fonctionnel="' + filepath + 'fragmentation_grain_fonctionnel.tif'+'"\n' )

            # self.checkBox_scenarioDiffs.isChecked()

            f.write('treatment='+treatment+'\n')

        f.close()
        return prop_file

    def control_parameters(self)->Union[str,None]:
        errors = ''
        if (self.radioButton_rasterMNHC.isChecked()  and self.inputMNHClayerfile.currentText() =="") \
            or (self.radioButton_dirMNHC.isChecked() and self.mQgsFileWidget_dirMNHC.filePath()==""):
            errors = errors + 'No MNHC input<br/>'
        dir = self.mQgsFileWidget_resultDir.filePath()
        if dir is None or dir=='':
            errors = errors + 'No output directory<br/>'
        if errors!='':
            return errors


    def run_grain(self)-> None:
        # init
        self.isInterrupted = False
        self.pushButton_interrupt.setEnabled(True)
        self.textEdit_journal.clear()
        self.tabWidget.setCurrentIndex(4)

        # control and run
        errors = self.control_parameters()
        if errors:
            self.pushInfo("Input errors :")
            self.pushInfo(errors)
        else:
            # run
            prop_file:str = self.create_properties_file()
            command: str = get_console_command(prop_file)
            run_command(command_line=command, feedback=self)

        # end
        self.pushButton_interrupt.setEnabled(False)
        self.setProgress(0)


    def interruptWork(self)-> None:
        self.isInterrupted = True
        self.pushButton_interrupt.setEnabled(False)

    def pushInfo(self, message: str) -> None:
        self.cursor.insertHtml( message + "<br/>\n")

    def pushCommandInfo(self, message: str) -> None:
        self.pushInfo('<span style="color:blue">**' + message + '**</span>\n')

    def pushConsoleInfo(self, message: str) -> None:
        self.pushInfo('<span style="color:grey">' + message + '</span>\n')

    def setProgress(self, progress: float) -> None:
        self.progressBar.setValue(progress)

    def isCanceled(self) -> bool:
        return self.isInterrupted
