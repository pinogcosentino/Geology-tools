# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   Lateral Spreading Analysis - QGIS Processing Algorithm                *
*   -----------------------------------------------------------           *
*   Date                 : 2026-02-07                                     *
*   Copyright            : (C) 2025 by Giuseppe Cosentino                 *
*   Email                : giuseppe.cosentino@cnr.it
*
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Giuseppe Cosentino'
__date__ = '2025-02-01'
__copyright__ = '(C) 2025 by Giuseppe Cosentino'
__revision__ = '$Format:%H$'

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterBoolean,
    QgsProcessingException
)
import os
import processing


class LateralSpreadingAlgorithm(QgsProcessingAlgorithm):
    """
    QGIS Processing Algorithm for Lateral Spreading Analysis in Seismic Microzonation.
    
    This algorithm classifies terrain into susceptibility zones based on:
    - Liquefaction Index (IL)
    - Slope percentage
    
    Output zones:
    - Z0 (Low Susceptibility Zones)
    - SZ (Susceptibility Zones)
    - RZ (Respect Zones)
    """
    
    # Input parameter names
    INPUT_DTM = 'digital_terrain_model_dtm'
    INPUT_IL_LAYER = 'layer_with_il_index'
    INPUT_IL_FIELD = 'il_index'
    INPUT_APPLY_STYLES = 'apply_styles'
    
    # Output parameter names
    OUTPUT_SLOPE = 'Slope'
    OUTPUT_ZONES = 'Sz_rz_lateral_spreading'
    
    # Zone classification criteria
    ZONE_CRITERIA = [
        # (code, name, IL_min, IL_max, slope_min, slope_max, formula_text)
        (101, 'RZ', 0, 2, 15, None, 'RZ=(0<IL<=2)and(slope>15)'),
        (102, 'RZ', 2, 5, 5, None, 'RZ=(2<IL<=5)and(slope>5)'),
        (103, 'RZ', 5, 15, 5, None, 'RZ=(5<IL<=15)and(Slope>5)'),
        (104, 'RZ', 15, None, 2, None, 'RZ=(IL>15)and(slope>2)'),
        (201, 'SZ', 0, 2, 5, 15, 'SZ=(0<IL<=2)and(5<slope<=15)'),
        (202, 'SZ', 2, 5, 2, 5, 'SZ=(2<IL<=5)and(2<slope<=5)'),
        (203, 'SZ', 5, 15, 2, 5, 'SZ=(5<IL<=15)and(2<slope<=5)'),
        (300, 'SZ0', 0, 2, 2, 5, 'SZ0=(0<IL<=2)and(2<slope<=5)'),
    ]

    def initAlgorithm(self, config=None):
        """Initialize algorithm parameters."""
        # Input raster layer (DTM)
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DTM,
                'Digital Terrain Model (DTM)',
                defaultValue=None
            )
        )
        
        # Input vector layer with liquefaction index
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_IL_LAYER,
                'Layer with Liquefaction Index (IL)',
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None
            )
        )
        
        # Field containing the liquefaction index
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_IL_FIELD,
                'Liquefaction Index Field',
                type=QgsProcessingParameterField.Numeric,
                parentLayerParameterName=self.INPUT_IL_LAYER,
                allowMultiple=False,
                defaultValue=None
            )
        )
        
        # Optional: Apply predefined styles
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INPUT_APPLY_STYLES,
                'Apply predefined styles to outputs',
                defaultValue=True
            )
        )
        
        # Output: Slope raster
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_SLOPE,
                'Slope (%)',
                createByDefault=True,
                defaultValue=None
            )
        )
        
        # Output: Susceptibility zones
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_ZONES,
                'Lateral Spreading Zones (SZ/RZ)',
                type=QgsProcessing.TypeVectorPolygon,
                createByDefault=True,
                supportsAppend=True,
                defaultValue='TEMPORARY_OUTPUT'
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        """Execute the algorithm."""
        # Initialize feedback with total steps
        total_steps = 10 + len(self.ZONE_CRITERIA) * 5  # Base steps + per-zone steps
        feedback = QgsProcessingMultiStepFeedback(total_steps, model_feedback)
        
        results = {}
        outputs = {}
        current_step = 0
        
        try:
            # Step 1: Clip DTM to IL layer extent
            feedback.setProgressText('Clipping DTM to analysis area...')
            clipped_dtm = self._clip_raster(
                parameters[self.INPUT_DTM],
                parameters[self.INPUT_IL_LAYER],
                context,
                feedback
            )
            outputs['clipped_dtm'] = clipped_dtm
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            if feedback.isCanceled():
                return {}
            
            # Step 2: Calculate slope
            feedback.setProgressText('Calculating slope...')
            slope_output = self._calculate_slope(
                clipped_dtm,
                parameters[self.OUTPUT_SLOPE],
                context,
                feedback
            )
            outputs['slope'] = slope_output
            results[self.OUTPUT_SLOPE] = slope_output
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            if feedback.isCanceled():
                return {}
            
            # Step 3: Apply style to slope (if requested)
            if parameters.get(self.INPUT_APPLY_STYLES, True):
                feedback.setProgressText('Applying style to slope layer...')
                self._apply_style(slope_output, 'slope.qml', context, feedback)
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            # Step 4: Polygonize slope raster
            feedback.setProgressText('Converting slope raster to polygons...')
            slope_polygons = self._polygonize_raster(slope_output, context, feedback)
            outputs['slope_polygons'] = slope_polygons
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            if feedback.isCanceled():
                return {}
            
            # Step 5: Intersect slope with IL layer
            feedback.setProgressText('Intersecting slope with liquefaction index layer...')
            intersected = self._intersect_layers(
                slope_polygons,
                parameters[self.INPUT_IL_LAYER],
                context,
                feedback
            )
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            # Step 6: Rename IL field for easier processing
            feedback.setProgressText('Preparing data...')
            prepared_data = self._rename_il_field(
                intersected,
                parameters[self.INPUT_IL_FIELD],
                context,
                feedback
            )
            outputs['prepared_data'] = prepared_data
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            if feedback.isCanceled():
                return {}
            
            # Step 7-N: Process each zone classification
            zone_layers = []
            for zone_config in self.ZONE_CRITERIA:
                code, zone_type, il_min, il_max, slope_min, slope_max, formula = zone_config
                
                feedback.setProgressText(f'Processing zone {code} ({zone_type})...')
                
                # Extract features matching criteria
                zone_layer = self._extract_zone(
                    prepared_data,
                    code,
                    il_min, il_max, slope_min, slope_max,
                    formula,
                    context,
                    feedback,
                    current_step
                )
                
                if zone_layer:
                    zone_layers.append(zone_layer)
                
                current_step += 5  # Each zone processing has 5 sub-steps
                feedback.setCurrentStep(current_step)
                
                if feedback.isCanceled():
                    return {}
            
            # Step N+1: Merge all zones
            feedback.setProgressText('Merging all zones...')
            merged_zones = self._merge_zones(zone_layers, context, feedback)
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            # Step N+2: Reorganize final fields
            feedback.setProgressText('Finalizing output...')
            final_output = self._reorganize_final_fields(
                merged_zones,
                parameters[self.OUTPUT_ZONES],
                context,
                feedback
            )
            results[self.OUTPUT_ZONES] = final_output
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            # Step N+3: Apply style to zones (if requested)
            if parameters.get(self.INPUT_APPLY_STYLES, True):
                feedback.setProgressText('Applying style to zones layer...')
                self._apply_style(final_output, 'style.qml', context, feedback)
            
            feedback.setProgressText('Analysis complete!')
            
        except Exception as e:
            raise QgsProcessingException(f'Error during processing: {str(e)}')
        
        return results

    # Helper methods for individual processing steps
    
    def _clip_raster(self, raster_input, mask_layer, context, feedback):
        """Clip raster to mask layer extent."""
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,
            'INPUT': raster_input,
            'KEEP_RESOLUTION': False,
            'MASK': mask_layer,
            'MULTITHREADING': False,
            'NODATA': None,
            'SOURCE_CRS': 'ProjectCrs',
            'TARGET_CRS': 'ProjectCrs',
            'TARGET_EXTENT': mask_layer,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        result = processing.run(
            'gdal:cliprasterbymasklayer',
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )
        return result['OUTPUT']
    
    def _calculate_slope(self, input_raster, output_path, context, feedback):
        """Calculate slope percentage from DTM."""
        alg_params = {
            'AS_PERCENT': True,
            'BAND': 1,
            'COMPUTE_EDGES': False,
            'INPUT': input_raster,
            'SCALE': 1,
            'ZEVENBERGEN': False,
            'OUTPUT': output_path
        }
        result = processing.run(
            'gdal:slope',
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )
        return result['OUTPUT']
    
    def _polygonize_raster(self, input_raster, context, feedback):
        """Convert raster to polygons."""
        alg_params = {
            'BAND': 1,
            'EIGHT_CONNECTEDNESS': False,
            'FIELD': 'DN',
            'INPUT': input_raster,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        result = processing.run(
            'gdal:polygonize',
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )
        return result['OUTPUT']
    
    def _intersect_layers(self, input_layer, overlay_layer, context, feedback):
        """Intersect two vector layers."""
        alg_params = {
            'GRID_SIZE': None,
            'INPUT': input_layer,
            'INPUT_FIELDS': [''],
            'OVERLAY': overlay_layer,
            'OVERLAY_FIELDS': [''],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        result = processing.run(
            'native:intersection',
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )
        return result['OUTPUT']
    
    def _rename_il_field(self, input_layer, il_field_name, context, feedback):
        """Rename IL field to standardized name."""
        alg_params = {
            'FIELD': il_field_name,
            'INPUT': input_layer,
            'NEW_NAME': 'INDEX',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        result = processing.run(
            'native:renametablefield',
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )
        return result['OUTPUT']
    
    def _build_expression(self, il_min, il_max, slope_min, slope_max):
        """Build SQL expression for zone extraction."""
        il_conditions = []
        slope_conditions = []
        
        # Build IL condition
        if il_min is not None and il_max is not None:
            il_conditions.append(f'"INDEX" > {il_min} AND "INDEX" <= {il_max}')
        elif il_min is not None:
            il_conditions.append(f'"INDEX" > {il_min}')
        elif il_max is not None:
            il_conditions.append(f'"INDEX" <= {il_max}')
        
        # Build slope condition
        if slope_min is not None and slope_max is not None:
            slope_conditions.append(f'"DN" > {slope_min} AND "DN" <= {slope_max}')
        elif slope_min is not None:
            slope_conditions.append(f'"DN" > {slope_min}')
        elif slope_max is not None:
            slope_conditions.append(f'"DN" <= {slope_max}')
        
        # Combine conditions
        expression_parts = []
        if il_conditions:
            expression_parts.append(f'({" AND ".join(il_conditions)})')
        if slope_conditions:
            expression_parts.append(f'({" AND ".join(slope_conditions)})')
        
        return ' AND '.join(expression_parts)
    
    def _extract_zone(self, input_layer, code, il_min, il_max, slope_min, slope_max, 
                      formula, context, feedback, base_step):
        """Extract and process a specific zone classification."""
        # Build extraction expression
        expression = self._build_expression(il_min, il_max, slope_min, slope_max)
        
        # Extract features
        alg_params = {
            'EXPRESSION': expression,
            'INPUT': input_layer,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        extract_result = processing.run(
            'native:extractbyexpression',
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )
        
        # Check if any features were extracted
        if not extract_result or not extract_result['OUTPUT']:
            return None
        
        # Dissolve
        alg_params = {
            'FIELD': [''],
            'INPUT': extract_result['OUTPUT'],
            'SEPARATE_DISJOINT': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        dissolve_result = processing.run(
            'native:dissolve',
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )
        
        # Add code field
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'code',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Double
            'FORMULA': str(code),
            'INPUT': dissolve_result['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        code_result = processing.run(
            'native:fieldcalculator',
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )
        
        # Reorganize fields
        alg_params = {
            'FIELDS_MAPPING': [
                {
                    'expression': '"fid"',
                    'length': 0,
                    'name': 'fid',
                    'precision': 0,
                    'type': 4  # int8
                },
                {
                    'expression': '"code"',
                    'length': 0,
                    'name': 'code',
                    'precision': 0,
                    'type': 6  # double
                }
            ],
            'INPUT': code_result['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        refactor_result = processing.run(
            'native:refactorfields',
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )
        
        # Add formula field
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'formula',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # String
            'FORMULA': f"'{formula}'",
            'INPUT': refactor_result['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        formula_result = processing.run(
            'native:fieldcalculator',
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )
        
        return formula_result['OUTPUT']
    
    def _merge_zones(self, zone_layers, context, feedback):
        """Merge all zone layers into one."""
        # Filter out None values
        valid_layers = [layer for layer in zone_layers if layer is not None]
        
        if not valid_layers:
            raise QgsProcessingException('No valid zones were generated')
        
        alg_params = {
            'CRS': 'ProjectCrs',
            'LAYERS': valid_layers,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        result = processing.run(
            'native:mergevectorlayers',
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )
        return result['OUTPUT']
    
    def _reorganize_final_fields(self, input_layer, output_path, context, feedback):
        """Reorganize and finalize output fields."""
        alg_params = {
            'FIELDS_MAPPING': [
                {
                    'expression': '"fid"',
                    'length': 0,
                    'name': 'fid',
                    'precision': 0,
                    'type': 4  # int8
                },
                {
                    'expression': '"code"',
                    'length': 0,
                    'name': 'code',
                    'precision': 0,
                    'type': 6  # double
                },
                {
                    'expression': '"formula"',
                    'length': 0,
                    'name': 'formula',
                    'precision': 0,
                    'type': 10  # text
                }
            ],
            'INPUT': input_layer,
            'OUTPUT': output_path
        }
        result = processing.run(
            'native:refactorfields',
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )
        return result['OUTPUT']
    
    def _apply_style(self, layer_output, style_filename, context, feedback):
        """Apply a QML style file to a layer."""
        style_path = os.path.join(os.path.dirname(__file__), "styles", style_filename)
        
        if not os.path.exists(style_path):
            feedback.pushWarning(f'Style file not found: {style_path}')
            return
        
        alg_params = {
            'INPUT': layer_output,
            'STYLE': style_path
        }
        try:
            processing.run(
                'native:setlayerstyle',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
        except Exception as e:
            feedback.pushWarning(f'Could not apply style: {str(e)}')

    # Algorithm metadata methods
    
    def name(self):
        """Internal algorithm name."""
        return 'lateral_spreading'

    def displayName(self):
        """User-friendly algorithm name."""
        return 'Lateral Spreading Analysis'

    def group(self):
        """Algorithm group."""
        return 'Seismic Microzonation'

    def groupId(self):
        """Internal group ID."""
        return 'seismic_microzonation'

    def shortHelpString(self):
        """Algorithm help string."""
        return """<html><body>
<h2>Lateral Spreading Analysis for Seismic Microzonation</h2>

<p>This tool calculates zones subject to lateral spreading based on liquefaction index (IL) 
and terrain slope percentage.</p>

<h3>Zone Classifications:</h3>

<p><b style="color:#33a02c;">A) Low Susceptibility Zones (Z0):</b></p>
<ul>
<li>2 &lt; Slope% ≤ 5 and 0 &lt; IL ≤ 2</li>
</ul>

<p><b style="color:#ff7f00;">B) Susceptibility Zones (SZ):</b></p>
<ul>
<li>0 &lt; IL ≤ 2 and 5 &lt; Slope% ≤ 15</li>
<li>2 &lt; IL ≤ 5 and 2 &lt; Slope% ≤ 5</li>
<li>5 &lt; IL ≤ 15 and 2 &lt; Slope% ≤ 5</li>
</ul>

<p><b style="color:#fc3300;">C) Respect Zones (RZ):</b></p>
<ul>
<li>0 &lt; IL ≤ 2 and Slope% &gt; 15</li>
<li>2 &lt; IL ≤ 5 and Slope% &gt; 5</li>
<li>5 &lt; IL ≤ 15 and Slope% &gt; 5</li>
<li>IL &gt; 15 and Slope% &gt; 2</li>
</ul>

<p><i>*IL = Liquefaction Index</i></p>

<h3>Inputs:</h3>
<ul>
<li><b>Digital Terrain Model (DTM):</b> Raster layer representing terrain elevation</li>
<li><b>Liquefaction Index Layer:</b> Polygon vector layer containing IL values</li>
<li><b>IL Field:</b> Numeric field in the vector layer containing liquefaction index values</li>
</ul>

<h3>Outputs:</h3>
<ul>
<li><b>Slope (%):</b> Raster layer showing terrain slope in percentage</li>
<li><b>Lateral Spreading Zones:</b> Polygon vector layer with classified zones (code and formula fields)</li>
</ul>

Version: 0.4 - 2026-02-12</i></p>
</body></html>"""

    def createInstance(self):
        """Create a new instance of the algorithm."""
        return LateralSpreadingAlgorithm()