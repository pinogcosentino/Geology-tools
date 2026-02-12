# -*- coding: utf-8 -*-

__author__ = 'Giuseppe Cosentino'
__date__ = '2026-02-12'
__copyright__ = '(C) 2026 by Giuseppe Cosentino'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import QgsProcessingProvider
import os
from qgis.PyQt.QtGui import QIcon
from .algorithms.hydrological_analysis_algorithm import HydrologicalAnalysisStreams
from .algorithms.ls4sm_algorithm import LateralSpreadingAlgorithm
from .algorithms.G4PL_algorithm import GeologyAlgorithm
from .algorithms.SZMG_algorithm import SeismicMicrozonationAlgorithm




class Geology_toolsProvider(QgsProcessingProvider):

    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        self.addAlgorithm(HydrologicalAnalysisStreams())
        self.addAlgorithm(LateralSpreadingAlgorithm())
        self.addAlgorithm(GeologyAlgorithm())
        self.addAlgorithm(SeismicMicrozonationAlgorithm())

        # add additional algorithms here
        # self.addAlgorithm(MyOtherAlgorithm())

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return 'geology_tools'

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return self.tr('Geology tools')

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QIcon(os.path.join(os.path.dirname(__file__), 'icon.png'))

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()
