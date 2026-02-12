# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   Geology from Points and Lines - QGIS Processing Algorithm             *
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

__author__ = 'Giuseppe Cosentino'
__date__ = '2025-01-15'
__copyright__ = '(C) 2025 by Giuseppe Cosentino'
__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsProcessingParameterEnum,
    QgsWkbTypes
)
import processing


class GeologyAlgorithm(QgsProcessingAlgorithm):
    """
    This algorithm generates geological polygons and contacts from point and line data.
    
    The workflow:
    1. Cleans duplicate geometries from input points
    2. Polygonizes line features to create enclosed areas
    3. Joins geological attributes from points to polygons
    4. Generates geological contact lines with attributes
    """

    # Constants for parameter names
    INPUT_POINTS = 'points_with_geological_information_centroid'
    INPUT_ATTRIBUTE = 'geological_attribute_input'
    INPUT_LINES = 'line_drawing_geological_contacts'
    TOLERANCE = 'vertex_tolerance'
    SPATIAL_PREDICATE = 'spatial_predicate'
    
    OUTPUT_POLYGONS = 'Polygons'
    OUTPUT_CLEAN_POINTS = 'CleanPoints'
    OUTPUT_SEGMENTS = 'SegmentsOfTheDrawingOfGeologicalContacts'
    OUTPUT_GEOLOGICAL_POLYGONS = 'GeologicalPolygons'
    OUTPUT_CONTACTS = 'GeologyContactsPointAttributes'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return GeologyAlgorithm()

    def name(self):
        return 'geology_from_point_and_line'

    def displayName(self):
        return self.tr('Geology from Points and Lines')

    def group(self):
        return self.tr('Geological Mapping')

    def group(self):
        return self.tr('Geological Mapping')

    def groupId(self):
        return 'geological_mapping'

    def shortHelpString(self):
        return self.tr("""
        <h2>Description</h2>
        <p>This algorithm creates a digital geological map from point and line data, 
        automating the generation of geological units and simplifying detailed geological mapping.</p>
        
        <h2>Workflow</h2>
        <ol>
        <li><b>Prepare line data:</b> Draw geological contact lines that intersect or touch 
        to form closed polygons</li>
        <li><b>Add point data:</b> Place points inside polygons with geological attributes 
        (formation codes, lithology, etc.)</li>
        <li><b>Run algorithm:</b> The tool will:
            <ul>
            <li>Clean duplicate geometries</li>
            <li>Create polygons from lines</li>
            <li>Transfer attributes from points to polygons</li>
            <li>Generate geological contact lines with attributes</li>
            </ul>
        </li>
        </ol>
        
        <h2>Parameters</h2>
        <p><b>Input Points:</b> Point layer containing geological information (centroids of units)</p>
        <p><b>Geological Attribute:</b> Field containing the geological classification</p>
        <p><b>Input Lines:</b> Line layer representing geological contacts</p>
        <p><b>Vertex Tolerance:</b> Distance threshold for removing duplicate vertices (meters)</p>
        <p><b>Spatial Predicate:</b> Method for joining attributes (intersects, contains, within)</p>
        
        <h2>Outputs</h2>
        <p><b>Geological Polygons:</b> Final polygons with geological attributes</p>
        <p><b>Geology Contacts:</b> Lines representing boundaries between geological units</p>
        <p><b>Other outputs:</b> Intermediate layers useful for quality control</p>
        
        <h2>Tips</h2>
        <ul>
        <li>Ensure lines form closed polygons without gaps</li>
        <li>Place one point per enclosed area</li>
        <li>Use appropriate vertex tolerance for your coordinate system</li>
        <li>Check intermediate outputs if results are unexpected</li>
        </ul>
        
        <p><i>Author: Giuseppe Cosentino (Pino)</i></p>
        <p><i>Version: 0.4 - 2026-02-12</i></p>
        """)

    def initAlgorithm(self, config=None):
        """
        Define inputs and outputs of the algorithm.
        """
        # Input parameters
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_POINTS,
                self.tr('Points with geological information (centroid)'),
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_ATTRIBUTE,
                self.tr('Geological attribute field'),
                type=QgsProcessingParameterField.Any,
                parentLayerParameterName=self.INPUT_POINTS,
                allowMultiple=False,
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LINES,
                self.tr('Line drawing (geological contacts)'),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None
            )
        )
        
        # Advanced parameters
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TOLERANCE,
                self.tr('Vertex tolerance (for duplicate removal)'),
                type=QgsProcessingParameterNumber.Double,
                minValue=0.0,
                defaultValue=0.000001,
                optional=False
            )
        )
        
        self.addParameter(
            QgsProcessingParameterEnum(
                self.SPATIAL_PREDICATE,
                self.tr('Spatial predicate for joining attributes'),
                options=[
                    self.tr('Intersects'),
                    self.tr('Contains'),
                    self.tr('Within'),
                    self.tr('Overlaps')
                ],
                defaultValue=0,
                optional=False
            )
        )
        
        # Output parameters
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_POLYGONS,
                self.tr('Polygons (intermediate)'),
                type=QgsProcessing.TypeVectorPolygon,
                createByDefault=True,
                defaultValue='TEMPORARY_OUTPUT'
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_CLEAN_POINTS,
                self.tr('Clean points (intermediate)'),
                type=QgsProcessing.TypeVectorPoint,
                createByDefault=True,
                defaultValue='TEMPORARY_OUTPUT'
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_SEGMENTS,
                self.tr('Segments of geological contacts (intermediate)'),
                type=QgsProcessing.TypeVectorLine,
                createByDefault=True,
                defaultValue='TEMPORARY_OUTPUT'
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_GEOLOGICAL_POLYGONS,
                self.tr('Geological polygons'),
                type=QgsProcessing.TypeVectorPolygon,
                createByDefault=True,
                supportsAppend=True,
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_CONTACTS,
                self.tr('Geology contacts (with attributes)'),
                type=QgsProcessing.TypeVectorLine,
                createByDefault=True,
                supportsAppend=True,
                defaultValue=None
            )
        )

    def validateInputs(self, parameters, context):
        """
        Validate input parameters before processing.
        """
        errors = {}
        
        # Check if input points layer has features
        points_source = self.parameterAsSource(parameters, self.INPUT_POINTS, context)
        if points_source and points_source.featureCount() == 0:
            errors[self.INPUT_POINTS] = self.tr('Input points layer is empty')
        
        # Check if input lines layer has features
        lines_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LINES, context)
        if lines_layer and lines_layer.featureCount() == 0:
            errors[self.INPUT_LINES] = self.tr('Input lines layer is empty')
        
        # Validate geometry types
        if points_source:
            geom_type = points_source.wkbType()
            if not (QgsWkbTypes.geometryType(geom_type) == QgsWkbTypes.PointGeometry):
                errors[self.INPUT_POINTS] = self.tr('Input must be a point layer')
        
        if lines_layer:
            geom_type = lines_layer.wkbType()
            if not (QgsWkbTypes.geometryType(geom_type) == QgsWkbTypes.LineGeometry):
                errors[self.INPUT_LINES] = self.tr('Input must be a line layer')
        
        return errors or {}

    def processAlgorithm(self, parameters, context, model_feedback):
        """
        Main processing algorithm.
        """
        try:
            # Validate inputs
            validation_errors = self.validateInputs(parameters, context)
            if validation_errors:
                error_msg = '\n'.join([f"{k}: {v}" for k, v in validation_errors.items()])
                raise QgsProcessingException(self.tr(f'Input validation failed:\n{error_msg}'))
            
            # Setup multi-step feedback
            feedback = QgsProcessingMultiStepFeedback(10, model_feedback)
            results = {}
            outputs = {}
            
            # Get parameters
            tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context)
            spatial_predicate = self.parameterAsEnum(parameters, self.SPATIAL_PREDICATE, context)
            
            # Step 1: Remove duplicate geometries from points
            feedback.setProgressText(self.tr('Step 1/10: Cleaning duplicate point geometries...'))
            alg_params = {
                'INPUT': parameters[self.INPUT_POINTS],
                'OUTPUT': parameters[self.OUTPUT_CLEAN_POINTS]
            }
            outputs['clean_points'] = processing.run(
                'native:deleteduplicategeometries',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            results[self.OUTPUT_CLEAN_POINTS] = outputs['clean_points']['OUTPUT']
            
            feedback.setCurrentStep(1)
            if feedback.isCanceled():
                return {}
            
            # Step 2: Polygonize lines
            feedback.setProgressText(self.tr('Step 2/10: Creating polygons from lines...'))
            alg_params = {
                'INPUT': parameters[self.INPUT_LINES],
                'KEEP_FIELDS': True,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['polygonize'] = processing.run(
                'native:polygonize',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            feedback.setCurrentStep(2)
            if feedback.isCanceled():
                return {}
            
            # Check if polygonization was successful
            if not outputs['polygonize']['OUTPUT']:
                raise QgsProcessingException(
                    self.tr('Polygonization failed. Check that lines form closed polygons.')
                )
            
            # Step 3: Remove duplicate polygon geometries
            feedback.setProgressText(self.tr('Step 3/10: Cleaning duplicate polygon geometries...'))
            alg_params = {
                'INPUT': outputs['polygonize']['OUTPUT'],
                'OUTPUT': parameters[self.OUTPUT_POLYGONS]
            }
            outputs['clean_polygons'] = processing.run(
                'native:deleteduplicategeometries',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            results[self.OUTPUT_POLYGONS] = outputs['clean_polygons']['OUTPUT']
            
            feedback.setCurrentStep(3)
            if feedback.isCanceled():
                return {}
            
            # Step 4: Join attributes by location
            feedback.setProgressText(self.tr('Step 4/10: Joining geological attributes to polygons...'))
            alg_params = {
                'DISCARD_NONMATCHING': True,
                'INPUT': outputs['clean_polygons']['OUTPUT'],
                'JOIN': outputs['clean_points']['OUTPUT'],
                'JOIN_FIELDS': [parameters[self.INPUT_ATTRIBUTE]],
                'METHOD': 0,  # Create separate feature for each matching feature (one-to-many)
                'PREDICATE': [spatial_predicate],
                'PREFIX': '',
                'OUTPUT': parameters[self.OUTPUT_GEOLOGICAL_POLYGONS]
            }
            outputs['join_attributes'] = processing.run(
                'native:joinattributesbylocation',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            results[self.OUTPUT_GEOLOGICAL_POLYGONS] = outputs['join_attributes']['OUTPUT']
            
            feedback.setCurrentStep(4)
            if feedback.isCanceled():
                return {}
            
            # Step 5: Convert polygons to lines
            feedback.setProgressText(self.tr('Step 5/10: Converting polygons to lines...'))
            alg_params = {
                'INPUT': outputs['join_attributes']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['polygons_to_lines'] = processing.run(
                'native:polygonstolines',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            feedback.setCurrentStep(5)
            if feedback.isCanceled():
                return {}
            
            # Step 6: Remove duplicate vertices
            feedback.setProgressText(self.tr('Step 6/10: Removing duplicate vertices...'))
            alg_params = {
                'INPUT': outputs['polygons_to_lines']['OUTPUT'],
                'TOLERANCE': tolerance,
                'USE_Z_VALUE': False,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['remove_duplicates'] = processing.run(
                'native:removeduplicatevertices',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            feedback.setCurrentStep(6)
            if feedback.isCanceled():
                return {}
            
            # Step 7: Explode lines
            feedback.setProgressText(self.tr('Step 7/10: Exploding lines into segments...'))
            alg_params = {
                'INPUT': outputs['remove_duplicates']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['explode_lines'] = processing.run(
                'native:explodelines',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            feedback.setCurrentStep(7)
            if feedback.isCanceled():
                return {}
            
            # Step 8: Remove duplicate line geometries
            feedback.setProgressText(self.tr('Step 8/10: Cleaning duplicate line segments...'))
            alg_params = {
                'INPUT': outputs['explode_lines']['OUTPUT'],
                'OUTPUT': parameters[self.OUTPUT_SEGMENTS]
            }
            outputs['clean_lines'] = processing.run(
                'native:deleteduplicategeometries',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            results[self.OUTPUT_SEGMENTS] = outputs['clean_lines']['OUTPUT']
            
            feedback.setCurrentStep(8)
            if feedback.isCanceled():
                return {}
            
            # Step 9: Dissolve by geological attribute
            feedback.setProgressText(self.tr('Step 9/10: Dissolving lines by geological attribute...'))
            alg_params = {
                'FIELD': parameters[self.INPUT_ATTRIBUTE],
                'INPUT': outputs['clean_lines']['OUTPUT'],
                'SEPARATE_DISJOINT': False,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['dissolve'] = processing.run(
                'native:dissolve',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            feedback.setCurrentStep(9)
            if feedback.isCanceled():
                return {}
            
            # Step 10: Convert multipart to singleparts
            feedback.setProgressText(self.tr('Step 10/10: Converting to single parts...'))
            alg_params = {
                'INPUT': outputs['dissolve']['OUTPUT'],
                'OUTPUT': parameters[self.OUTPUT_CONTACTS]
            }
            outputs['multipart_to_singleparts'] = processing.run(
                'native:multiparttosingleparts',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            results[self.OUTPUT_CONTACTS] = outputs['multipart_to_singleparts']['OUTPUT']
            
            feedback.setProgressText(self.tr('Processing complete!'))
            return results
            
        except QgsProcessingException as e:
            feedback.reportError(str(e), fatalError=True)
            raise
        except Exception as e:
            feedback.reportError(
                self.tr(f'Unexpected error occurred: {str(e)}'),
                fatalError=True
            )
            raise QgsProcessingException(str(e))

    def helpUrl(self):
        return ''
