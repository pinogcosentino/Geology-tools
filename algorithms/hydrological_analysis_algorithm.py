# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   Hydrological Analysis Streams - QGIS Processing Algorithm             *
*   -----------------------------------------------------------           *
*   Date                 : 2026-02-07                                     *
*   Copyright            : (C) 2025 by Giuseppe Cosentino                 *
*   Email                : giuseppe.cosentino@cnr.it                      *
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""


from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorDestination,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException
)
from qgis.PyQt.QtCore import QCoreApplication
import processing


class HydrologicalAnalysisStreams(QgsProcessingAlgorithm):
    """
    Algorithm for hydrological analysis that generates the drainage network
    from a digital terrain model (DTM).
    """
    
    # Costanti per i nomi dei parametri
    INPUT_DTM = 'digital_terrain_model_dtm'
    MIN_SLOPE = 'minimum_slope_degree'
    MIN_BASIN_SIZE = 'minimum_size_of_exterior_watershed_basin'
    ITERATIONS = 'iterations'
    MAX_ANGLE = 'maximum_node_corner_vertex_angle'
    OFFSET = 'offset'
    OUTPUT_VECTOR_RAW = 'VectorStreamRaw'
    OUTPUT_STREAM = 'DelineateStream'
    OUTPUT_DRAINAGE = 'DrainageDirection'
    OUTPUT_HALF_BASIN = 'HalfBasin'
    OUTPUT_TCI = 'TopographicIndexLnaTanb'
    OUTPUT_SMOOTH = 'SmoothStreams'
    OUTPUT_FILLED_DTM = 'FilledDtmWangLiu'

    def tr(self, string):
        """Returns a translated string."""
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return HydrologicalAnalysisStreams()

    def name(self):
        return 'Hydrological Analysis - Stream Network'

    def displayName(self):
        return self.tr('Hydrological Analysis - Stream Network')

    def group(self):
        return self.tr('Hydrology')

    def groupId(self):
        return 'hydrology'

    def shortHelpString(self):
        """Returns a short description of the algorithm."""
        return self.tr(
            'This algorithm performs a complete hydrological analysis on a DTM to extract:\n\n'
            '• Vector stream network (raw and smoothed)\n'
            '• Drainage directions\n'
            '• Topographic index ln(a/tan(b))\n'
            '• Half basins\n\n'
            'Main steps:\n'
            '1. Fill sinks (Wang & Liu algorithm)\n'
            '2. Flow calculation and stream delineation\n'
            '3. Raster to vector conversion\n'
            '4. Geometry smoothing'
        )

    def initAlgorithm(self, config=None):
        """Defines the input and output parameters of the algorithm."""
        
        # Main input
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DTM,
                self.tr('Digital Terrain Model (DTM)'),
                defaultValue=None
            )
        )
        
        # Numerical parameters
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_SLOPE,
                self.tr('Minimum slope (degrees)'),
                type=QgsProcessingParameterNumber.Double,
                minValue=0.01,
                maxValue=90,
                defaultValue=0.1
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_BASIN_SIZE,
                self.tr('Minimum basin size (cells)'),
                type=QgsProcessingParameterNumber.Integer,
                minValue=1,
                defaultValue=100
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.ITERATIONS,
                self.tr('Smoothing iterations'),
                type=QgsProcessingParameterNumber.Integer,
                minValue=1,
                maxValue=10,
                defaultValue=1
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_ANGLE,
                self.tr('Maximum vertex angle (degrees)'),
                type=QgsProcessingParameterNumber.Integer,
                minValue=0,
                maxValue=360,
                defaultValue=180
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.OFFSET,
                self.tr('Smoothing offset'),
                type=QgsProcessingParameterNumber.Double,
                minValue=0.01,
                maxValue=1.0,
                defaultValue=0.25
            )
        )
        
        # Main outputs
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT_VECTOR_RAW,
                self.tr('Raw stream network (vector)'),
                type=QgsProcessing.TypeVectorLine,
                createByDefault=True,
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_SMOOTH,
                self.tr('Smoothed stream network'),
                type=QgsProcessing.TypeVectorLine,
                createByDefault=True,
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_FILLED_DTM,
                self.tr('Filled DTM (Wang & Liu)'),
                createByDefault=True,
                defaultValue=None
            )
        )
        
        # Optional outputs
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_STREAM,
                self.tr('Stream network (raster)'),
                optional=True,
                createByDefault=True,
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_DRAINAGE,
                self.tr('Drainage directions'),
                optional=True,
                createByDefault=True,
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_HALF_BASIN,
                self.tr('Half basins'),
                optional=True,
                createByDefault=True,
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_TCI,
                self.tr('Topographic index ln(a/tan(b))'),
                optional=True,
                createByDefault=True,
                defaultValue=None
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        """Executes the hydrological analysis algorithm."""
        
        # Initialize multi-step feedback
        feedback = QgsProcessingMultiStepFeedback(4, model_feedback)
        results = {}
        outputs = {}

        try:
            # STEP 1: Fill sinks (Wang & Liu) - ALGORITMO AGGIORNATO
            feedback.pushInfo(self.tr('Step 1/4: Filling DTM depressions (Wang & Liu)...'))
            
            alg_params = {
                'BAND': 1,
                'INPUT': parameters[self.INPUT_DTM],
                'MIN_SLOPE': parameters[self.MIN_SLOPE],
                'CREATION_OPTIONS': None,
                'OUTPUT_FILLED_DEM': parameters[self.OUTPUT_FILLED_DTM]
            }
            
            outputs['FillSinksWangLiu'] = processing.run(
                'native:fillsinkswangliu',  # CAMBIATO DA 'sagang:fillsinkswangliu'
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            # Verifica che l'output sia valido
            if not outputs['FillSinksWangLiu'] or 'OUTPUT_FILLED_DEM' not in outputs['FillSinksWangLiu']:
                raise QgsProcessingException(
                    self.tr('Error: Fill sinks algorithm did not produce valid output')
                )
            
            results[self.OUTPUT_FILLED_DTM] = outputs['FillSinksWangLiu']['OUTPUT_FILLED_DEM']
            
            feedback.setCurrentStep(1)
            if feedback.isCanceled():
                return {}

            # STEP 2: Flow analysis with r.watershed
            feedback.pushInfo(self.tr('Step 2/4: Computing flow and delineating streams...'))
            
            alg_params = {
                '-4': False,
                '-a': False,
                '-b': False,
                '-m': False,
                '-s': False,
                'GRASS_RASTER_FORMAT_META': '',
                'GRASS_RASTER_FORMAT_OPT': '',
                'GRASS_REGION_CELLSIZE_PARAMETER': 0,
                'GRASS_REGION_PARAMETER': None,
                'blocking': None,
                'convergence': 5,
                'depression': None,
                'disturbed_land': None,
                'elevation': outputs['FillSinksWangLiu']['OUTPUT_FILLED_DEM'],  # AGGIORNATO
                'flow': None,
                'max_slope_length': None,
                'memory': 300,
                'threshold': parameters[self.MIN_BASIN_SIZE],
                'drainage': parameters[self.OUTPUT_DRAINAGE],
                'half_basin': parameters[self.OUTPUT_HALF_BASIN],
                'stream': parameters[self.OUTPUT_STREAM],
                'tci': parameters[self.OUTPUT_TCI]
            }
            
            outputs['Rwatershed'] = processing.run(
                'grass:r.watershed',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            results[self.OUTPUT_STREAM] = outputs['Rwatershed']['stream']
            results[self.OUTPUT_DRAINAGE] = outputs['Rwatershed']['drainage']
            results[self.OUTPUT_HALF_BASIN] = outputs['Rwatershed']['half_basin']
            results[self.OUTPUT_TCI] = outputs['Rwatershed']['tci']
            
            feedback.setCurrentStep(2)
            if feedback.isCanceled():
                return {}

            # STEP 3: Raster to vector conversion
            feedback.pushInfo(self.tr('Step 3/4: Converting stream network to vector...'))
            
            alg_params = {
                '-b': False,
                '-s': False,
                '-t': False,
                '-v': False,
                '-z': False,
                'GRASS_OUTPUT_TYPE_PARAMETER': 0,  # auto
                'GRASS_REGION_CELLSIZE_PARAMETER': 0,
                'GRASS_REGION_PARAMETER': None,
                'GRASS_VECTOR_DSCO': '',
                'GRASS_VECTOR_EXPORT_NOCAT': False,
                'GRASS_VECTOR_LCO': '',
                'column': 'value',
                'input': outputs['Rwatershed']['stream'],
                'type': 0,  # line
                'output': parameters[self.OUTPUT_VECTOR_RAW]
            }
            
            outputs['Rtovect'] = processing.run(
                'grass:r.to.vect',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            results[self.OUTPUT_VECTOR_RAW] = outputs['Rtovect']['output']
            
            feedback.setCurrentStep(3)
            if feedback.isCanceled():
                return {}

            # STEP 4: Geometry smoothing
            feedback.pushInfo(self.tr('Step 4/4: Smoothing stream network...'))
            
            alg_params = {
                'INPUT': outputs['Rtovect']['output'],
                'ITERATIONS': parameters[self.ITERATIONS],
                'MAX_ANGLE': parameters[self.MAX_ANGLE],
                'OFFSET': parameters[self.OFFSET],
                'OUTPUT': parameters[self.OUTPUT_SMOOTH]
            }
            
            outputs['SmoothStream'] = processing.run(
                'native:smoothgeometry',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            results[self.OUTPUT_SMOOTH] = outputs['SmoothStream']['OUTPUT']
            
            feedback.pushInfo(self.tr('✓ Hydrological analysis completed successfully!'))
            
            return results
            
        except Exception as e:
            raise QgsProcessingException(
                self.tr(f'Error during processing: {str(e)}')
            )