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

import functools

from PyQt4 import QtGui

from qgis.core import (
    QgsMessageLog,
    QgsFeatureRequest,
    QgsExpression,
    QgsMapLayerRegistry,
    QGis,
)

from qgis.gui import (
    QgsMessageBar,
)

from qgis_plugin_base import Plugin
# from settings_dialog import *
from identify_tool import IdentifyTool
from ngq_manager_client import NGQManagerClient
import resources_rc


class IPCPlugin(Plugin):
    def __init__(self, iface):
        super(IPCPlugin, self).__init__(iface, "IPC Plugin")
        self.scaleFactor = 100000

    def initGui(self):
        self.workerExt = NGQManagerClient()
        self.workerExt.commandResived.connect(self.tryProcessCommand)

        self._iface.projectRead.connect(
            self.workerExt.setProjectFile
        )
        self._iface.newProjectCreated.connect(
            self.workerExt.setProjectFile
        )
        self.workerExt.setProjectFile()

        self._iface.mapCanvas().layersChanged.connect(self.updateLayersHandle)

        self.actionRun = QtGui.QAction("Select object", self._iface.mainWindow())
        self.actionRun.setIcon(QtGui.QIcon(":/plugins/ipcplugin/icons/info.png"))
        self.actionRun.setEnabled(False)
        self.actionSettings = QtGui.QAction('Settings', self._iface.mainWindow())
        self.actionSettings.setIcon(QtGui.QIcon(':/plugins/ipcplugin/icons/settings.png'))

        # self._iface.addPluginToMenu(self.getPluginName(), self.actionSettings)
        self._iface.addToolBarIcon(self.actionRun)

        self.actionRun.triggered.connect(self.run)
        self.actionSettings.triggered.connect(self.showSettings)

        self.mapTool = IdentifyTool(self._iface)
        self.mapTool.identified.connect(self.identifyResultProcess)
        self.mapTool.avalableChanged.connect(self.actionRun.setEnabled)

        self.updateLayersHandle()

    def unload(self):
        self._iface.mapCanvas().layersChanged.disconnect(self.updateLayersHandle)

        self._iface.removeToolBarIcon(self.actionRun)
        # self.iface.removePluginMenu(self.getPluginName(), self.actionSettings)

        if self._iface.mapCanvas().mapTool() == self.mapTool:
            self.mapTool.disconnectAll()
            self._iface.mapCanvas().unsetMapTool(self.mapTool)

        self.workerExt.disconnect()
        self.workerExt = None
    # def getCSLayers(self):
    #     csLayerName = getCSLayerName()
    #     return QgsMapLayerRegistry.instance().mapLayersByName(csLayerName)

    # def getRZLayers(self):
    #     rzLayerName = getRZLayerName()
    #     return QgsMapLayerRegistry.instance().mapLayersByName(rzLayerName)

    def getTargetLayersForIdentification(self):
        # layers = []
        # layers.extend(
        #     self.getCSLayers()
        # )
        # layers.extend(
        #     self.getRZLayers()
        # )

        # layers = [layer for layer in layers if layer.type() == layer.VectorLayer]
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        layers = [layer for layer in layers if layer.type() == layer.VectorLayer]
        # layers = [layer for layer in layers if layer.geometryType() == QGis.Point]
        return layers

    def updateLayersHandle(self):
        targetLayers = self.getTargetLayersForIdentification()
        self.mapTool.setLayers(targetLayers)

    def tryProcessCommand(self, command):
        Plugin().plPrint("tryProcessCommand: " + str(command))

        if command.get("name") == u'activate':
            self.activateMainWindow()
        elif command.get("name") == u'position':
            self.zoomTo(command.get("args"))
        else:
            Plugin().plPrint("Warnning: Unknown command: " + unicode(command.get("name")))

    def getTargetLayersForPosition(self):
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        layers = [layer for layer in layers if layer.type() == layer.VectorLayer]
        return layers

    def zoomTo(self, args):
        Plugin().plPrint("Zoom to object: " + str(args))

        expr = " and ".join(['"%s" = \'%s\'' % (unicode(k), unicode(v)) for k, v in args.items()])
        Plugin().plPrint("expr: " + expr)
        expr = QgsExpression(expr)
        req = QgsFeatureRequest(expr)

        qgsFeaturesCount = 0
        qgsFeatures = []
        for targetLayer in self.getTargetLayersForPosition():
            Plugin().plPrint("Searche in " + targetLayer.name() + " layer")
            qgsFeatureIterator = targetLayer.getFeatures(req)
            for qgsFeature in qgsFeatureIterator:
                qgsFeatures.append([qgsFeature, targetLayer])
                qgsFeaturesCount += 1

            Plugin().plPrint("qgsFeatures: " + str(qgsFeatures))

        if qgsFeaturesCount == 0:
            self.showMessageForUser("No object is found!", QgsMessageBar.WARNING)
            Plugin().plPrint("There is no feature with args %s" % str(args), QgsMessageLog.WARNING)
        elif qgsFeaturesCount == 1:
            self.zoom2feature(
                qgsFeatures[0][1],
                qgsFeatures[0][0]
            )
        else:
            self.showMessageForUser("Found more then one object!", QgsMessageBar.WARNING)
            Plugin().plPrint("There are %d features with %s" % (qgsFeaturesCount, args,), QgsMessageLog.WARNING)
            self.zoom2feature(
                qgsFeatures[0][1],
                qgsFeatures[0][0]
            )

        self.activateMainWindow()

    def zoom2feature(self, qgsLayer, qgsFeature):
        qgsLayer.setSelectedFeatures([qgsFeature.id()])

        self._iface.mapCanvas().zoomToSelected(qgsLayer)

        if self._iface.mapCanvas().scale() > self.scaleFactor:
            self._iface.mapCanvas().zoomScale(self.scaleFactor)

    def activateMainWindow(self):

        # self._iface.mainWindow().setWindowState(
        #     self._iface.mainWindow().windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive
        # )
        # setWindowFlags(Qt::WindowStaysOnTopHint);

        # self._iface.mainWindow().activateWindow()
        # self._iface.mainWindow().raise_()
        window = self._iface.mainWindow()
        window.showMinimized()
        window.showMaximized()

    def run(self):
        self._iface.mapCanvas().setMapTool(self.mapTool)

    def showSettings(self):
        # dlg = SettingsDialog(self._iface.mainWindow())
        # dlg.exec_()
        # self.updateLayersHandle()
        pass

    def identifyResultProcess(self, identifyResults):
        Plugin().plPrint("Identification results: " + str(identifyResults))

        guids = []
        layers = []
        for result in identifyResults:
            try:
                guid = result.mFeature.attribute(u"GUID")
                guids.append(guid)
                layers.append(result.mLayer.name())
            except KeyError:
                pass

        guidsCount = len(guids)

        if guidsCount == 0:
            self.showMessageForUser("No object is identified!", QgsMessageBar.WARNING, 0)
            Plugin().plPrint("There is no identifyed features", QgsMessageLog.WARNING)
        elif guidsCount == 1:
            self.getActionMenu(guids[0]).exec_(QtGui.QCursor.pos())
        else:
            resultsView = QtGui.QListWidget()
            resultsView.setWindowTitle("Identification results")
            resultsView.setAlternatingRowColors(True)
            resultsView.setResizeMode(QtGui.QListView.Adjust)
            resultsView.setSpacing(1)
            for guidIndex in range(0, len(guids)):
                resultsView.addItem("%s [%s]" % (guids[guidIndex], layers[guidIndex], ))

            resultsView.setMinimumWidth(
                resultsView.sizeHintForColumn(0) + 10
            )
            resultsView.setMinimumHeight(
                resultsView.sizeHintForRow(0) * resultsView.count() + 10
            )

            resultsView.itemClicked.connect(
                lambda item: self.getActionMenu(
                    guids[resultsView.row(item)]
                ).exec_(QtGui.QCursor.pos())
            )
            resultsView.show()
            # self.showMessageForUser("Identified more then one object!", QgsMessageBar.WARNING, 0)
            # Plugin().plPrint("There are %d features found. Only first got" % guidsCount, QgsMessageLog.WARNING)

    def getActionMenu(self, guid):
        menu = QtGui.QMenu()
        showObjectCard = QtGui.QAction("Show object card", menu)
        showObjectCard.setEnabled(False)
        showBalanceedDocument = QtGui.QAction("Show balanced document", menu)
        showBalanceedDocument.setEnabled(False)

        showObjectCard.setEnabled(True)
        showObjectCard.triggered.connect(
            functools.partial(self.sendShowcardURI, guid)
        )
        showBalanceedDocument.setEnabled(True)
        showBalanceedDocument.triggered.connect(
            functools.partial(self.showBalanceedDocumentActionProcess, guid)
        )

        menu.addAction(showObjectCard)
        menu.addAction(showBalanceedDocument)

        return menu

    def sendShowcardURI(self, guid):
        uri = "visidata:showcard?id=96094?guid=%s" % str(guid)
        self.workerExt.sendURICommand(uri)

    def showBalanceedDocumentActionProcess(self, guid):
        uri = "visidata:showcard?guid=58414BD65C3BBED34D89769A2607DD4A?guid=%s" % str(guid)
        self.workerExt.sendURICommand(uri)
