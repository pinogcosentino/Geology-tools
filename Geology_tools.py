# -*- coding: utf-8 -*-

__author__ = 'Giuseppe Cosentino'
__date__ = '2026-02-12'
__copyright__ = '(C) 2026 by Giuseppe Cosentino'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import sys
import inspect

from qgis.core import QgsProcessingAlgorithm, QgsApplication
from .Geology_tools_provider import Geology_toolsProvider


class Geology_toolsPlugin(object):

    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        self.provider = Geology_toolsProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
