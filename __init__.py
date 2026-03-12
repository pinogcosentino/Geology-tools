# -*- coding: utf-8 -*-

def classFactory(iface):
    from .Geology_tools import Geology_tools
    return Geology_tools(iface)
