# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis import gui


class IdentifyTool(gui.QgsMapToolIdentify):

    avalableChanged = pyqtSignal(bool)
    identified = pyqtSignal(list)

    def __init__(self, iface):
        gui.QgsMapToolIdentify.__init__(self, iface.mapCanvas())

        # self.cursor = QCursor(QPixmap(":/icons/cursor.png"), 1, 1)
        self.legend = iface.legendInterface()

        self.canvas().layersChanged.connect(self.__checkAvalable)
        self.canvas().currentLayerChanged.connect(self.__checkAvalable)

        self.__targetLayers = []

    # def activate(self):
    #     self.canvas().setCursor(self.cursor)

    def disconnectAll(self):
        self.canvas().layersChanged.disconnect(self.__checkAvalable)
        self.canvas().currentLayerChanged.disconnect(self.__checkAvalable)

    def setLayers(self, qgsVectorLayers):
        self.__targetLayers = qgsVectorLayers
        self.__checkAvalable()

    def canvasReleaseEvent(self, event):
        results = self.identify(event.x(), event.y(), self.__targetLayers, self.TopDownAll)
        self.identified.emit(results)

    def isAvalable(self):
        if len(self.__targetLayers) == 0:
            return False

        return True

    def __checkAvalable(self):
        self.avalableChanged.emit(self.isAvalable())
