from qgis.PyQt import uic
from qgis.PyQt import QtWidgets,QtCore
from qgis.core import QgsMapLayerProxyModel,QgsVectorLayer
from qgis.PyQt.QtWidgets import QWidget,QVBoxLayout,QLabel,QHBoxLayout,QPushButton,QFileDialog
from qgis.gui import QgsMapLayerComboBox
from pathlib import Path

class InputLayerFileWidget(QWidget):
    def __init__(self, parent=None):
        self.parent = parent
        QWidget.__init__(self)
        self.h_layout = QHBoxLayout()
        self.mlcb = QgsMapLayerComboBox(self)
        self.file_selection_button = QPushButton("\u2026", self)
        self.file_selection_button.setMaximumWidth(30)
        self.file_selection_button.setToolTip('Select from file')
        for c in self.children():
            self.h_layout.addWidget(c)
        self.setLayout(self.h_layout)
        
        self.file_selection_button.clicked.connect(self.getFile)

    def setFilters(self,filters):
        self.mlcb.setFilters(filters)
        if filters == QgsMapLayerProxyModel.RasterLayer:
            self.filters = '*.tif,*.asc'
        else:
            self.filters = '*.shp'

    def getFile(self):
        file_name = QFileDialog.getOpenFileName(None, 'Select file', '', filter=self.filters)
        if file_name:
            self.mlcb.setAdditionalItems([file_name[0]])
            self.mlcb.setCurrentIndex(self.mlcb.model().rowCount()-1)
                
    def currentLayer(self):
        layer = self.mlcb.currentLayer()
        if layer is not None:
            return layer
        else:
            path = self.mlcb.currentText()
            name = Path(path).stem
            layer = QgsVectorLayer(path, name, 'ogr')
            if layer.isValid():
                return layer
        return None
    
    def connectLayerChangedSlot(self,setLayerSlot):
        self.mlcb.layerChanged.connect(setLayerSlot)
