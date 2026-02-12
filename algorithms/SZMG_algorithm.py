# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   Seismic Microzonation Morphological Analysis - QGIS Algorithm         *
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


__author__ = 'Giuseppe Cosentino (Pino)'
__date__ = '2025-02-01'
__copyright__ = '(C) 2025 by Giuseppe Cosentino (Pino)'
__revision__ = '$Format:%H$'

from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFeatureSink)
import processing

class SeismicMicrozonationAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        # Input Raster (DTM)
        self.addParameter(QgsProcessingParameterRasterLayer(
            'digital__terrain_model_raster_input', 
            'Digital Terrain Model (DTM) Input', 
            defaultValue=None))
        
        # Input Vector (Zones)
        self.addParameter(QgsProcessingParameterVectorLayer(
            'geological_seismic_zones_vector_input', 
            'Geological/Seismic Zones (Vector)', 
            types=[QgsProcessing.TypeVectorPolygon], 
            defaultValue=None))
        
        # Dynamic Threshold
        self.addParameter(QgsProcessingParameterNumber(
            'slope_threshold', 
            'Slope Threshold for Instability (°)', 
            type=QgsProcessingParameterNumber.Double, 
            defaultValue=15.0, 
            minValue=0, 
            maxValue=90))

        # Output Raster
        self.addParameter(QgsProcessingParameterRasterDestination(
            'Slope', 
            'Calculated Slope Map (°)', 
            createByDefault=True))
        
        # Output Vector
        self.addParameter(QgsProcessingParameterFeatureSink(
            'Zs_Final', 
            'Seismic Microzones (Slope >= Threshold)', 
            type=QgsProcessing.TypeVectorAnyGeometry, 
            createByDefault=True))

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(7, model_feedback)
        results = {}
        outputs = {}
        
        threshold = self.parameterAsDouble(parameters, 'slope_threshold', context)

        # 1. Clip Raster by Mask
        alg_params = {
            'INPUT': parameters['digital__terrain_model_raster_input'],
            'MASK': parameters['geological_seismic_zones_vector_input'],
            'CROP_TO_CUTLINE': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Clipped'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled(): return {}

        # 2. Generate Slope
        alg_params = {
            'INPUT': outputs['Clipped']['OUTPUT'],
            'OUTPUT': parameters['Slope']
        }
        outputs['Slope'] = processing.run('gdal:slope', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Slope'] = outputs['Slope']['OUTPUT']

        feedback.setCurrentStep(2)
        if feedback.isCanceled(): return {}

        # 3. Raster Calculator (Applying dynamic threshold)
        alg_params = {
            'EXPRESSION': f'"A@1" >= {threshold}',
            'LAYERS': [outputs['Slope']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Calc'] = processing.run('native:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled(): return {}

        # 4. Polygonize (Raster to Vector)
        alg_params = {
            'INPUT': outputs['Calc']['OUTPUT'],
            'FIELD': 'DN',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Poly'] = processing.run('gdal:polygonize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled(): return {}

        # 5. Extract by Attribute (DN=1)
        alg_params = {
            'INPUT': outputs['Poly']['OUTPUT'],
            'FIELD': 'DN', 'OPERATOR': 0, 'VALUE': '1',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Extracted'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled(): return {}

        # 6. Dissolve (Clean up geometry)
        alg_params = {
            'INPUT': outputs['Extracted']['OUTPUT'],
            'FIELD': [],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dissolved'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled(): return {}

        # 7. Join Attributes by Location
        alg_params = {
            'INPUT': outputs['Dissolved']['OUTPUT'],
            'JOIN': parameters['geological_seismic_zones_vector_input'],
            'PREDICATE': [0], # Intersects
            'OUTPUT': parameters['Zs_Final']
        }
        outputs['Final'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        
        results['Zs_Final'] = outputs['Final']['OUTPUT']
        return results

    def name(self):
        return 'seismic_microzonation_morphology'

    def displayName(self):
        return 'Seismic Microzonation: Morphological Analysis'

    def group(self):
        return 'Seismic Microzonation'

    def groupId(self):
        return 'seismic_microzonation'

    def shortHelpString(self):
        return """<html>
<body>
<h2>Seismic Microzonation: Morphological Analysis</h2>
<p>This algorithm identifies areas with slopes exceeding a critical threshold (e.g., 15°) within seismic or geological zones.</p>

<h3>Workflow:</h3>
<ul>
  <li><b>Clipping:</b> The DTM is clipped using the geological vector mask layer.</li>
  <li><b>Slope Calculation:</b> A slope map is generated in degrees.</li>
  <li><b>Threshold Analysis:</b> Areas exceeding the user-defined slope value are isolated.</li>
  <li><b>Vectorization & Cleaning:</b> Identified areas are converted to polygons, dissolved for cleaner geometry, and spatially joined with input vector data to preserve original attributes.</li>
</ul>

<p><b>Notes:</b> This tool is designed for identifying areas susceptible to topographic amplification or slope instability according to Seismic Microzonation Guidelines.</p>

<br/>
</body>
</html>"""

    def createInstance(self):
        return SeismicMicrozonationAlgorithm()