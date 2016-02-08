# -*- coding: utf-8 -*-
def classFactory(iface):
    from plugin import IPCPlugin
    return IPCPlugin(iface)
