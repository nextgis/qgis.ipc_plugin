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

import os
import json

from PyQt4 import QtCore
from PyQt4 import QtNetwork

from qgis.core import (
    QgsProject,
)

from qgis_plugin_base import Plugin


class NGQManagerClient(QtCore.QObject):
    commandResived = QtCore.pyqtSignal(dict)

    def __init__(self):
        super(NGQManagerClient, self).__init__()

        self.socket = QtNetwork.QTcpSocket()
        self.socket.readyRead.connect(self.__readFromServer)
        self.socket.connected.connect(self.__connectEstablished)
        self.socket.disconnected.connect(self.__connectLost)
        self.socket.stateChanged.connect(self.__socetStateChange)

        self.__tryConnect()

        self.__qgisState = {}
        self.setQGISPID()

    def __tryConnect(self):
        host = "localhost"
        port = 9999
        Plugin().plPrint("Try connect to %s:%d" % (host, port))
        self.socket.connectToHost(host, port)

    def __connectLost(self):
        Plugin().plPrint("Connection lost")

    def __connectEstablished(self):
        Plugin().plPrint("Connection established: " + str(self.socket.socketDescriptor()))
        self.sendQGISState()

    def __socetStateChange(self, state):
        Plugin().plPrint("Socet state change to: " + str(state))
        if state == QtNetwork.QAbstractSocket.UnconnectedState:
            self.__tryConnect()

    def __readFromServer(self):
        data = unicode(self.socket.readAll())
        for line in data.split('\n')[:-1]:
            try:
                struct = json.loads(unicode(line))

                command = struct.get("command")
                if command is not None:
                    self.commandResived.emit(command)
                else:
                    Plugin().plPrint("Warnning: Unknown message: " + unicode(struct))
            except:
                Plugin().plPrint("ERROR: Cann't parse line: " + unicode(line))

        # responce = QtCore.QByteArray("Ok!")
        # self.socket.write(responce)

    def sendQGISState(self):
        Plugin().plPrint("Send QGIS state: " + str(self.__qgisState))
        data = json.dumps({"qgis_state": self.__qgisState})
        message = QtCore.QByteArray(data)
        self.socket.write(message + "\n")

    def disconnect(self):
        self.socket.blockSignals(True)
        self.socket.readyRead.disconnect(self.__readFromServer)
        self.socket.connected.disconnect(self.__connectEstablished)
        self.socket.disconnected.disconnect(self.__connectLost)
        self.socket.stateChanged.disconnect(self.__socetStateChange)

        self.socket.disconnectFromHost()
        self.socket.close()

    def setQGISPID(self):
        pid = int(QtCore.QCoreApplication.applicationPid())
        self.__qgisState.update({u"pid": pid})
        self.sendQGISState()

    def setProjectFile(self):
        projectFilename = os.path.abspath(QgsProject.instance().fileName())
        self.__qgisState.update({u"open_project": projectFilename})
        self.sendQGISState()

    def sendURICommand(self, uri):
        Plugin().plPrint("Send URI command: " + str(uri))
        data = json.dumps(
            {
                "command": {
                    "name": "send_uri",
                    "args": uri
                }
            }
        )

        message = QtCore.QByteArray(data)
        Plugin().plPrint("Message for send: " + str(message))
        self.socket.write(message + "\n")
