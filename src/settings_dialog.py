# -*- coding: utf-8 -*-
#******************************************************************************
#
# IPCPlugin
# ---------------------------------------------------------
# This plugin takes coordinates of a mouse click and gets information about all 
# objects from this point from OSM using Overpass API.
#
# Author:   Alexander Lisovenko, alexander.lisovenko@nextgis.ru
# *****************************************************************************
# Copyright (c) 2012-2015. NextGIS, info@nextgis.com
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# A copy of the GNU General Public License is available on the World Wide Web
# at <http://www.gnu.org/licenses/>. You can also obtain it by writing
# to the Free Software Foundation, 51 Franklin Street, Suite 500 Boston,
# MA 02110-1335 USA.
#
#******************************************************************************

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.gui import (
    QgsMapLayerProxyModel,
    QgsMapLayerComboBox,
    QgsFieldComboBox
)

from qgis.core import (
    QgsMapLayerRegistry,
)

def getCSLayerName():
    """ compressor staitions """
    return QSettings().value("ipc_plugin/csTargetLayerName", "")

def setCSLayerName(layerName):
    QSettings().setValue("ipc_plugin/csTargetLayerName", layerName)

def getCSIdField():
    """ compressor staitions id field name """
    return QSettings().value("ipc_plugin/csIdField", "")

def setCSIdField(fieldName):
    QSettings().setValue("ipc_plugin/csIdField", fieldName)

def getRZLayerName():
    """ responsibility zone """
    return QSettings().value("ipc_plugin/rzTargetLayerName", "")

def setRZLayerName(layerName):
    QSettings().setValue("ipc_plugin/rzTargetLayerName", layerName)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        self.resize(500, 100)
        self.setWindowTitle("Settings")

        layout = QGridLayout(self)

        csTargetLayerName = getCSLayerName()
        bufferTargetLayerName = getRZLayerName()

        csLable = QLabel("Compressor staitions layer:")
        csLable.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(csLable, 0, 0)
        self.__csLayerName = QgsMapLayerComboBox()
        self.__csLayerName.setEditable(True)
        self.__csLayerName.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.__csLayerName.setEditText(csTargetLayerName)
        self.__csLayerName.layerChanged.connect(self.csLayerChooze)
        self.__csLayerName.editTextChanged.connect(self.csLayernameSave)
        self.__csLayerName.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(self.__csLayerName, 0, 1)

        self.__csIdField = QgsFieldComboBox()
        self.__csIdField.setEditable(True)
        self.__csIdField.fieldChanged.connect(self.csIdFiledChooze)
        self.__csIdField.editTextChanged.connect(self.csIdFieldSave)
        self.__csIdField.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.csIdFieldFill()
        layout.addWidget(self.__csIdField, 0, 2)

        bufferLable = QLabel("Buffer layer:")
        bufferLable.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(bufferLable, 1, 0)
        # self.__bufferLayerName = QLineEdit(bufferTargetLayerName, self)
        # self.__bufferLayerName.editingFinished.connect(self.bufferTargetLayernameSave)
        self.__bufferLayerName = QgsMapLayerComboBox()
        self.__bufferLayerName.setEditable(True)
        self.__bufferLayerName.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.__bufferLayerName.setEditText(bufferTargetLayerName)
        self.__bufferLayerName.layerChanged.connect(self.bufferLayerChooze)
        self.__bufferLayerName.editTextChanged.connect(self.bufferLayernameSave)
        layout.addWidget(self.__bufferLayerName, 1, 1)

    def csLayerChooze(self, qgsMapLayer):
        self.__csLayerName.setEditText(qgsMapLayer.name())

    def csLayernameSave(self, csTargetLayerName):
        if csTargetLayerName == u"":
            return
        setCSLayerName(csTargetLayerName)
        self.csIdFieldFill()

    def csIdFieldFill(self):
        csIdField = getCSIdField()
        csTargetLayerName = getCSLayerName()
        layers = QgsMapLayerRegistry.instance().mapLayersByName(csTargetLayerName)
        if len(layers) > 0:
            self.__csIdField.setLayer(layers[0])
        else:
            self.__csIdField.setLayer(None)
        self.__csIdField.setEditText(csIdField)

    def csIdFiledChooze(self, fieldName):
        self.__csIdField.setEditText(fieldName)

    def csIdFieldSave(self, fieldName):
        settings = QSettings()
        if fieldName == u"":
            return
        setCSIdField(fieldName)

    def bufferLayerChooze(self, qgsMapLayer):
        self.__bufferLayerName.setEditText(qgsMapLayer.name())

    def bufferLayernameSave(self, bufferTargetLayerName):
        settings = QSettings()
        if bufferTargetLayerName == u"":
            return
        setRZLayerName(bufferTargetLayerName)
