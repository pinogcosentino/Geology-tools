# -*- coding: utf-8 -*-

__author__ = 'Giuseppe Cosentino'
__date__ = '2026-02-12'
__copyright__ = '(C) 2026 by Giuseppe Cosentino'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load Geology_tools class from file Geology_tools.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .Geology_tools import Geology_toolsPlugin
    return Geology_toolsPlugin(iface)
