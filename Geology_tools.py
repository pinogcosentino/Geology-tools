# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Geology Tools - Main Plugin File con toolbar dedicata
 (C) 2026 by Giuseppe Cosentino
***************************************************************************/
"""

import os
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsApplication
from .Geology_tools_provider import Geology_toolsProvider


class Geology_tools:

    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.toolbar = None
        self.actions = []

    def initProcessing(self):
        """Registra il provider nel Processing Framework."""
        self.provider = Geology_toolsProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        """Crea la toolbar e aggiunge un pulsante per ogni algoritmo."""
        self.initProcessing()

        # Toolbar dedicata al plugin
        self.toolbar = self.iface.addToolBar('Geology Tools')
        self.toolbar.setObjectName('GeologyToolsToolbar')

        # ------------------------------------------------------------------
        # Configurazione algoritmi:
        #   'algorithm_id' -> 'provider_id:algorithm_name()' (tutto minuscolo)
        #   'label'        -> tooltip e voce nel menu Plugins
        #   'icon'         -> file icona nella cartella del plugin
        #                     (fallback su icon.png se il file non esiste)
        # ------------------------------------------------------------------
        algorithms_config = [
            {
                'algorithm_id': 'geology_tools:hydrological_analysis_stream_network',
                'label': 'Hydrological Analysis - Stream Network (HASN)',
                'icon': 'icon.hasn.png',
            },
            {
                'algorithm_id': 'geology_tools:lateral_spreading_analysis',
                'label': 'Lateral Spreading Analysis (LSA)',
                'icon': 'icon.lsa.png',
            },
            {
                'algorithm_id': 'geology_tools:geology_from_points_and_lines',
                'label': 'Geology from Points and Lines',
                'icon': 'icon.g4pl.png',
            },
            {
                'algorithm_id': 'geology_tools:seismic_microzonation_morphology',
                'label': 'Seismic Microzonation Morphological Analysis (SMMA)',
                'icon': 'icon.smma.png',
            },
        ]

        plugin_dir = os.path.dirname(__file__)

        for cfg in algorithms_config:
            icon_path = os.path.join(plugin_dir, cfg['icon'])

            # Fallback sull'icona generica se quella specifica non esiste
            if not os.path.exists(icon_path):
                icon_path = os.path.join(plugin_dir, 'icon.png')

            action = QAction(
                QIcon(icon_path),
                cfg['label'],
                self.iface.mainWindow()
            )
            action.setToolTip(cfg['label'])

            algo_id = cfg['algorithm_id']
            action.triggered.connect(
                lambda checked, aid=algo_id: self.run_algorithm(aid)
            )

            self.toolbar.addAction(action)
            self.iface.addPluginToMenu('Geology Tools', action)
            self.actions.append(action)

    def unload(self):
        """Rimuove toolbar, azioni e provider alla disattivazione del plugin."""
        for action in self.actions:
            self.iface.removePluginMenu('Geology Tools', action)

        if self.toolbar:
            self.toolbar.deleteLater()
            self.toolbar = None

        self.actions.clear()
        QgsApplication.processingRegistry().removeProvider(self.provider)

    def run_algorithm(self, algorithm_id):
        """
        Apre la finestra di dialogo dell'algoritmo specificato.
        Se l'ID non è trovato mostra un avviso nella message bar di QGIS.
        """
        from qgis import processing

        algo = QgsApplication.processingRegistry().algorithmById(algorithm_id)
        if not algo:
            self.iface.messageBar().pushWarning(
                'Geology Tools',
                f'Algoritmo "{algorithm_id}" non trovato.'
            )
            return

        processing.execAlgorithmDialog(algorithm_id)
