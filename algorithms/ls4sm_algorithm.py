
# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   Lateral Spreading Analysis - QGIS Processing Algorithm                *
*   -----------------------------------------------------------           *
*   Date                 : 2026-02-13                                     *
*   Copyright            : (C) 2026 by Giuseppe Cosentino                 *
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
__date__ = '2026-02-13'
__copyright__ = '(C) 2026 by Giuseppe Cosentino'
__version__ = '1.0'

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import os

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
    QgsProcessingException,
    QgsMessageLog,
    Qgis,
    QgsVectorLayer
)
import processing


class ZoneType(Enum):
    """Enumeration of lateral spreading zone types."""
    LOW_SUSCEPTIBILITY = "Z0"  # Low Susceptibility Zones
    SUSCEPTIBILITY = "SZ"      # Susceptibility Zones
    RESPECT = "RZ"             # Respect Zones


@dataclass
class ZoneClassification:
    """
    Data class representing a zone classification criterion.
    
    Attributes:
        code: Unique numeric identifier for the zone
        zone_type: Type of zone (Z0, SZ, RZ)
        il_min: Minimum liquefaction index (None if no lower bound)
        il_max: Maximum liquefaction index (None if no upper bound)
        slope_min: Minimum slope percentage (None if no lower bound)
        slope_max: Maximum slope percentage (None if no upper bound)
        formula_text: Human-readable formula description
    """
    code: int
    zone_type: ZoneType
    il_min: Optional[float]
    il_max: Optional[float]
    slope_min: Optional[float]
    slope_max: Optional[float]
    formula_text: str
    
    def get_zone_name(self) -> str:
        """Get the zone type name."""
        return self.zone_type.value
    
    def get_zone_description(self) -> str:
        """Get a human-readable description of the zone criteria."""
        il_desc = self._format_range("IL", self.il_min, self.il_max)
        slope_desc = self._format_range("Slope%", self.slope_min, self.slope_max)
        return f"{self.get_zone_name()}: {il_desc} and {slope_desc}"
    
    @staticmethod
    def _format_range(param_name: str, min_val: Optional[float], 
                     max_val: Optional[float]) -> str:
        """Format a parameter range as a string."""
        if min_val is not None and max_val is not None:
            return f"{min_val} < {param_name} ≤ {max_val}"
        elif min_val is not None:
            return f"{param_name} > {min_val}"
        elif max_val is not None:
            return f"{param_name} ≤ {max_val}"
        return param_name


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
    
    Reference: Italian Seismic Microzonation Guidelines
    """
    
    # Input parameter names
    INPUT_DTM = 'digital_terrain_model_dtm'
    INPUT_IL_LAYER = 'layer_with_il_index'
    INPUT_IL_FIELD = 'il_index'
    INPUT_APPLY_STYLES = 'apply_styles'
    
    # Output parameter names
    OUTPUT_SLOPE = 'slope_output'
    OUTPUT_ZONES = 'zones_output'
    
    # Field names
    FIELD_DN = 'DN'
    FIELD_INDEX = 'INDEX'
    FIELD_FID = 'fid'
    FIELD_CODE = 'code'
    FIELD_FORMULA = 'formula'
    
    # Processing steps
    STEP_CLIP = 0
    STEP_SLOPE = 1
    STEP_STYLE_SLOPE = 2
    STEP_POLYGONIZE = 3
    STEP_INTERSECT = 4
    STEP_RENAME = 5
    STEP_ZONES_START = 6
    
    # Zone classification criteria
    # Format: (code, zone_type, IL_min, IL_max, slope_min, slope_max, formula_text)
    ZONE_CRITERIA = [
        ZoneClassification(101, ZoneType.RESPECT, 0, 2, 15, None, 
                          'RZ=(0<IL≤2) and (slope>15)'),
        ZoneClassification(102, ZoneType.RESPECT, 2, 5, 5, None, 
                          'RZ=(2<IL≤5) and (slope>5)'),
        ZoneClassification(103, ZoneType.RESPECT, 5, 15, 5, None, 
                          'RZ=(5<IL≤15) and (slope>5)'),
        ZoneClassification(104, ZoneType.RESPECT, 15, None, 2, None, 
                          'RZ=(IL>15) and (slope>2)'),
        ZoneClassification(201, ZoneType.SUSCEPTIBILITY, 0, 2, 5, 15, 
                          'SZ=(0<IL≤2) and (5<slope≤15)'),
        ZoneClassification(202, ZoneType.SUSCEPTIBILITY, 2, 5, 2, 5, 
                          'SZ=(2<IL≤5) and (2<slope≤5)'),
        ZoneClassification(203, ZoneType.SUSCEPTIBILITY, 5, 15, 2, 5, 
                          'SZ=(5<IL≤15) and (2<slope≤5)'),
        ZoneClassification(300, ZoneType.LOW_SUSCEPTIBILITY, 0, 2, 2, 5, 
                          'Z0=(0<IL≤2) and (2<slope≤5)'),
    ]

    def __init__(self):
        """Initialize the algorithm."""
        super().__init__()

    def initAlgorithm(self, config: Optional[Dict] = None) -> None:
        """
        Initialize algorithm parameters.
        
        Args:
            config: Optional configuration dictionary
        """
        # Input raster layer (DTM)
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DTM,
                self.tr('Digital Terrain Model (DTM)'),
                defaultValue=None
            )
        )
        
        # Input vector layer with liquefaction index
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_IL_LAYER,
                self.tr('Layer with Liquefaction Index (IL)'),
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None
            )
        )
        
        # Field containing the liquefaction index
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_IL_FIELD,
                self.tr('Liquefaction Index Field'),
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
                self.tr('Apply predefined styles to outputs'),
                defaultValue=True
            )
        )
        
        # Output: Slope raster
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_SLOPE,
                self.tr('Slope (%)'),
                createByDefault=True,
                defaultValue=None
            )
        )
        
        # Output: Susceptibility zones
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_ZONES,
                self.tr('Lateral Spreading Zones (Z0/SZ/RZ)'),
                type=QgsProcessing.TypeVectorPolygon,
                createByDefault=True,
                supportsAppend=True,
                defaultValue='TEMPORARY_OUTPUT'
            )
        )

    def processAlgorithm(
        self, 
        parameters: Dict[str, Any], 
        context: Any, 
        model_feedback: Any
    ) -> Dict[str, Any]:
        """
        Execute the lateral spreading analysis algorithm.
        
        Args:
            parameters: Dictionary of input parameters
            context: Processing context
            model_feedback: Feedback object for progress reporting
            
        Returns:
            Dictionary containing output results
            
        Raises:
            QgsProcessingException: If processing fails at any step
        """
        # Validate inputs
        self._validate_parameters(parameters)
        
        # Calculate total steps
        steps_per_zone = 5  # Extract, dissolve, add code, refactor, add formula
        total_steps = (
            self.STEP_ZONES_START + 
            len(self.ZONE_CRITERIA) * steps_per_zone + 
            4  # merge, reorganize, style zones, finalize
        )
        
        feedback = QgsProcessingMultiStepFeedback(total_steps, model_feedback)
        results = {}
        outputs = {}
        current_step = 0
        
        try:
            # Step 1: Clip DTM to IL layer extent
            feedback.pushInfo(self.tr('Step 1/{}: Clipping DTM to analysis area...').format(total_steps))
            outputs['clipped_dtm'] = self._clip_raster(
                parameters[self.INPUT_DTM],
                parameters[self.INPUT_IL_LAYER],
                context,
                feedback
            )
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            if feedback.isCanceled():
                return {}
            
            # Step 2: Calculate slope
            feedback.pushInfo(self.tr('Step 2/{}: Calculating slope percentage...').format(total_steps))
            outputs['slope'] = self._calculate_slope(
                outputs['clipped_dtm'],
                parameters[self.OUTPUT_SLOPE],
                context,
                feedback
            )
            results[self.OUTPUT_SLOPE] = outputs['slope']
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            if feedback.isCanceled():
                return {}
            
            # Step 3: Apply style to slope (if requested)
            if parameters.get(self.INPUT_APPLY_STYLES, True):
                feedback.pushInfo(self.tr('Step 3/{}: Applying style to slope layer...').format(total_steps))
                self._apply_style(outputs['slope'], 'slope.qml', context, feedback)
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            # Step 4: Polygonize slope raster
            feedback.pushInfo(self.tr('Step 4/{}: Converting slope raster to polygons...').format(total_steps))
            outputs['slope_polygons'] = self._polygonize_raster(
                outputs['slope'], 
                context, 
                feedback
            )
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            if feedback.isCanceled():
                return {}
            
            # Step 5: Intersect slope with IL layer
            feedback.pushInfo(self.tr('Step 5/{}: Intersecting slope with liquefaction index layer...').format(total_steps))
            outputs['intersected'] = self._intersect_layers(
                outputs['slope_polygons'],
                parameters[self.INPUT_IL_LAYER],
                context,
                feedback
            )
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            # Step 6: Rename IL field for easier processing
            feedback.pushInfo(self.tr('Step 6/{}: Preparing data for zone classification...').format(total_steps))
            outputs['prepared_data'] = self._rename_il_field(
                outputs['intersected'],
                parameters[self.INPUT_IL_FIELD],
                context,
                feedback
            )
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            if feedback.isCanceled():
                return {}
            
            # Step 7-N: Process each zone classification
            zone_layers = []
            for i, zone_config in enumerate(self.ZONE_CRITERIA, 1):
                feedback.pushInfo(
                    self.tr('Processing zone {}/{}: {} (code: {})...').format(
                        i, 
                        len(self.ZONE_CRITERIA),
                        zone_config.get_zone_name(),
                        zone_config.code
                    )
                )
                
                zone_layer = self._extract_and_process_zone(
                    outputs['prepared_data'],
                    zone_config,
                    context,
                    feedback
                )
                
                if zone_layer:
                    zone_layers.append(zone_layer)
                    feedback.pushInfo(
                        self.tr('  ✓ Zone {} processed successfully').format(zone_config.code)
                    )
                else:
                    feedback.pushInfo(
                        self.tr('  ⓘ No features found for zone {}').format(zone_config.code)
                    )
                
                current_step += steps_per_zone
                feedback.setCurrentStep(current_step)
                
                if feedback.isCanceled():
                    return {}
            
            # Validate zone extraction
            if not zone_layers:
                raise QgsProcessingException(
                    self.tr('No zones were generated. Check input data and IL field values.')
                )
            
            # Step N+1: Merge all zones
            feedback.pushInfo(self.tr('Merging all {} zone layers...').format(len(zone_layers)))
            outputs['merged_zones'] = self._merge_zones(zone_layers, context, feedback)
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            # Step N+2: Reorganize final fields
            feedback.pushInfo(self.tr('Finalizing output fields...'))
            outputs['final'] = self._reorganize_final_fields(
                outputs['merged_zones'],
                parameters[self.OUTPUT_ZONES],
                context,
                feedback
            )
            results[self.OUTPUT_ZONES] = outputs['final']
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            # Step N+3: Apply style to zones (if requested)
            if parameters.get(self.INPUT_APPLY_STYLES, True):
                feedback.pushInfo(self.tr('Applying style to zones layer...'))
                self._apply_style(outputs['final'], 'lateral_spreading.qml', context, feedback)
            current_step += 1
            feedback.setCurrentStep(current_step)
            
            # Summary
            feedback.pushInfo('')
            feedback.pushInfo(self.tr('═' * 60))
            feedback.pushInfo(self.tr('✓ Lateral Spreading Analysis completed successfully!'))
            feedback.pushInfo(self.tr('  - {} zones classified and merged').format(len(zone_layers)))
            feedback.pushInfo(self.tr('  - Slope map generated'))
            feedback.pushInfo(self.tr('═' * 60))
            
        except QgsProcessingException:
            raise
        except Exception as e:
            error_msg = self.tr('Unexpected error during processing: {}').format(str(e))
            self._log_error(error_msg)
            raise QgsProcessingException(error_msg)
        
        return results

    # ========================================================================
    # Validation Methods
    # ========================================================================
    
    def _validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Validate input parameters before processing.
        
        Args:
            parameters: Dictionary of input parameters
            
        Raises:
            QgsProcessingException: If validation fails
        """
        # Check DTM
        if not parameters.get(self.INPUT_DTM):
            raise QgsProcessingException(
                self.tr('Digital Terrain Model (DTM) is required')
            )
        
        # Check IL layer
        if not parameters.get(self.INPUT_IL_LAYER):
            raise QgsProcessingException(
                self.tr('Liquefaction Index layer is required')
            )
        
        # Check IL field
        if not parameters.get(self.INPUT_IL_FIELD):
            raise QgsProcessingException(
                self.tr('Liquefaction Index field must be specified')
            )

    # ========================================================================
    # Core Processing Methods
    # ========================================================================
    
    def _clip_raster(
        self, 
        raster_input: str, 
        mask_layer: str, 
        context: Any, 
        feedback: Any
    ) -> str:
        """
        Clip raster to mask layer extent.
        
        Args:
            raster_input: Input raster layer
            mask_layer: Vector mask layer
            context: Processing context
            feedback: Feedback object
            
        Returns:
            Path to clipped raster
        """
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Use input layer data type
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
    
    def _calculate_slope(
        self, 
        input_raster: str, 
        output_path: str, 
        context: Any, 
        feedback: Any
    ) -> str:
        """
        Calculate slope percentage from DTM.
        
        Args:
            input_raster: Input DTM raster
            output_path: Output path for slope raster
            context: Processing context
            feedback: Feedback object
            
        Returns:
            Path to slope raster
        """
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
    
    def _polygonize_raster(
        self, 
        input_raster: str, 
        context: Any, 
        feedback: Any
    ) -> str:
        """
        Convert raster to polygons.
        
        Args:
            input_raster: Input raster layer
            context: Processing context
            feedback: Feedback object
            
        Returns:
            Path to polygonized vector layer
        """
        alg_params = {
            'BAND': 1,
            'EIGHT_CONNECTEDNESS': False,
            'FIELD': self.FIELD_DN,
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
    
    def _intersect_layers(
        self, 
        input_layer: str, 
        overlay_layer: str, 
        context: Any, 
        feedback: Any
    ) -> str:
        """
        Intersect two vector layers.
        
        Args:
            input_layer: Input vector layer
            overlay_layer: Overlay vector layer
            context: Processing context
            feedback: Feedback object
            
        Returns:
            Path to intersected layer
        """
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
    
    def _rename_il_field(
        self, 
        input_layer: str, 
        il_field_name: str, 
        context: Any, 
        feedback: Any
    ) -> str:
        """
        Rename IL field to standardized name.
        
        Args:
            input_layer: Input vector layer
            il_field_name: Original IL field name
            context: Processing context
            feedback: Feedback object
            
        Returns:
            Path to layer with renamed field
        """
        alg_params = {
            'FIELD': il_field_name,
            'INPUT': input_layer,
            'NEW_NAME': self.FIELD_INDEX,
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

    # ========================================================================
    # Zone Classification Methods
    # ========================================================================
    
    def _build_extraction_expression(
        self, 
        zone_config: ZoneClassification
    ) -> str:
        """
        Build SQL expression for zone extraction.
        
        Args:
            zone_config: Zone classification configuration
            
        Returns:
            SQL WHERE expression string
        """
        conditions = []
        
        # Build IL condition
        il_cond = self._build_range_condition(
            self.FIELD_INDEX, 
            zone_config.il_min, 
            zone_config.il_max
        )
        if il_cond:
            conditions.append(il_cond)
        
        # Build slope condition
        slope_cond = self._build_range_condition(
            self.FIELD_DN, 
            zone_config.slope_min, 
            zone_config.slope_max
        )
        if slope_cond:
            conditions.append(slope_cond)
        
        return ' AND '.join(conditions) if conditions else '1=1'
    
    @staticmethod
    def _build_range_condition(
        field_name: str, 
        min_val: Optional[float], 
        max_val: Optional[float]
    ) -> str:
        """
        Build SQL range condition for a field.
        
        Args:
            field_name: Name of the field
            min_val: Minimum value (None if no lower bound)
            max_val: Maximum value (None if no upper bound)
            
        Returns:
            SQL condition string
        """
        if min_val is not None and max_val is not None:
            return f'("{field_name}" > {min_val} AND "{field_name}" <= {max_val})'
        elif min_val is not None:
            return f'"{field_name}" > {min_val}'
        elif max_val is not None:
            return f'"{field_name}" <= {max_val}'
        return ''
    
    def _extract_and_process_zone(
        self, 
        input_layer: str,
        zone_config: ZoneClassification,
        context: Any,
        feedback: Any
    ) -> Optional[str]:
        """
        Extract and process a specific zone classification.
        
        This method performs the complete workflow for a single zone:
        1. Extract features matching criteria
        2. Dissolve geometries
        3. Add zone code
        4. Refactor fields
        5. Add formula description
        
        Args:
            input_layer: Input vector layer with IL and slope data
            zone_config: Zone classification configuration
            context: Processing context
            feedback: Feedback object
            
        Returns:
            Path to processed zone layer, or None if no features match
        """
        try:
            # Step 1: Extract features matching criteria
            expression = self._build_extraction_expression(zone_config)
            
            extract_params = {
                'EXPRESSION': expression,
                'INPUT': input_layer,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            extract_result = processing.run(
                'native:extractbyexpression',
                extract_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            if not extract_result or not extract_result['OUTPUT']:
                return None
            
            # Step 2: Dissolve geometries
            dissolve_params = {
                'FIELD': [''],
                'INPUT': extract_result['OUTPUT'],
                'SEPARATE_DISJOINT': True,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            dissolve_result = processing.run(
                'native:dissolve',
                dissolve_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            # Step 3: Add zone code field
            code_params = {
                'FIELD_LENGTH': 0,
                'FIELD_NAME': self.FIELD_CODE,
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 0,  # Double
                'FORMULA': str(zone_config.code),
                'INPUT': dissolve_result['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            code_result = processing.run(
                'native:fieldcalculator',
                code_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            # Step 4: Refactor fields to keep only necessary ones
            refactor_params = {
                'FIELDS_MAPPING': [
                    {
                        'expression': f'"{self.FIELD_FID}"',
                        'length': 0,
                        'name': self.FIELD_FID,
                        'precision': 0,
                        'type': 4  # int8
                    },
                    {
                        'expression': f'"{self.FIELD_CODE}"',
                        'length': 0,
                        'name': self.FIELD_CODE,
                        'precision': 0,
                        'type': 6  # double
                    }
                ],
                'INPUT': code_result['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            refactor_result = processing.run(
                'native:refactorfields',
                refactor_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            # Step 5: Add formula description field
            formula_params = {
                'FIELD_LENGTH': 255,
                'FIELD_NAME': self.FIELD_FORMULA,
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 2,  # String
                'FORMULA': f"'{zone_config.formula_text}'",
                'INPUT': refactor_result['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            formula_result = processing.run(
                'native:fieldcalculator',
                formula_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            return formula_result['OUTPUT']
            
        except Exception as e:
            feedback.pushWarning(
                self.tr('Error processing zone {}: {}').format(zone_config.code, str(e))
            )
            return None
    
    def _merge_zones(
        self, 
        zone_layers: List[str], 
        context: Any, 
        feedback: Any
    ) -> str:
        """
        Merge all zone layers into one.
        
        Args:
            zone_layers: List of zone layer paths
            context: Processing context
            feedback: Feedback object
            
        Returns:
            Path to merged layer
            
        Raises:
            QgsProcessingException: If no valid zones were generated
        """
        # Filter out None values
        valid_layers = [layer for layer in zone_layers if layer is not None]
        
        if not valid_layers:
            raise QgsProcessingException(
                self.tr('No valid zones were generated. Check input data.')
            )
        
        if len(valid_layers) == 1:
            # Only one layer, no need to merge
            return valid_layers[0]
        
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
    
    def _reorganize_final_fields(
        self, 
        input_layer: str, 
        output_path: str, 
        context: Any, 
        feedback: Any
    ) -> str:
        """
        Reorganize and finalize output fields.
        
        Args:
            input_layer: Input vector layer
            output_path: Output path
            context: Processing context
            feedback: Feedback object
            
        Returns:
            Path to final output layer
        """
        alg_params = {
            'FIELDS_MAPPING': [
                {
                    'expression': f'"{self.FIELD_FID}"',
                    'length': 0,
                    'name': self.FIELD_FID,
                    'precision': 0,
                    'type': 4  # int8
                },
                {
                    'expression': f'"{self.FIELD_CODE}"',
                    'length': 0,
                    'name': self.FIELD_CODE,
                    'precision': 0,
                    'type': 6  # double
                },
                {
                    'expression': f'"{self.FIELD_FORMULA}"',
                    'length': 255,
                    'name': self.FIELD_FORMULA,
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

    # ========================================================================
    # Style Management Methods
    # ========================================================================
    
    def _apply_style(
        self, 
        layer_output: str, 
        style_filename: str, 
        context: Any, 
        feedback: Any
    ) -> None:
        """
        Apply a QML style file to a layer.
        
        Args:
            layer_output: Output layer path
            style_filename: Style filename (e.g., 'slope.qml')
            context: Processing context
            feedback: Feedback object
        """
        style_path = os.path.join(
            os.path.dirname(__file__), 
            "styles", 
            style_filename
        )
        
        if not os.path.exists(style_path):
            feedback.pushWarning(
                self.tr('Style file not found: {}').format(style_path)
            )
            return
        
        try:
            alg_params = {
                'INPUT': layer_output,
                'STYLE': style_path
            }
            processing.run(
                'native:setlayerstyle',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
        except Exception as e:
            feedback.pushWarning(
                self.tr('Could not apply style {}: {}').format(style_filename, str(e))
            )

    # ========================================================================
    # Logging Methods
    # ========================================================================
    
    def _log_error(self, message: str) -> None:
        """
        Log error message.
        
        Args:
            message: Error message to log
        """
        QgsMessageLog.logMessage(
            message, 
            self.displayName(), 
            Qgis.Critical
        )
    
    def _log_warning(self, message: str) -> None:
        """
        Log warning message.
        
        Args:
            message: Warning message to log
        """
        QgsMessageLog.logMessage(
            message, 
            self.displayName(), 
            Qgis.Warning
        )
    
    def _log_info(self, message: str) -> None:
        """
        Log info message.
        
        Args:
            message: Info message to log
        """
        QgsMessageLog.logMessage(
            message, 
            self.displayName(), 
            Qgis.Info
        )

    # ========================================================================
    # Algorithm Metadata Methods
    # ========================================================================
    
    def name(self) -> str:
        """Return internal algorithm name."""
        return 'lateral_spreading_analysis'

    def displayName(self) -> str:
        """Return user-friendly algorithm name."""
        return self.tr('Lateral Spreading Analysis (LSA)')

    def group(self) -> str:
        """Return algorithm group."""
        return self.tr('Seismic Microzonation')

    def groupId(self) -> str:
        """Return internal group ID."""
        return 'seismic_microzonation'

    def shortHelpString(self) -> str:
        """Return algorithm help documentation."""
        help_text = """<html><body>
<h2>Lateral Spreading Analysis for Seismic Microzonation</h2>

<p>This algorithm classifies terrain susceptibility to lateral spreading phenomena 
based on liquefaction index (IL) and terrain slope percentage.</p>

<h3>Zone Classifications:</h3>

<div style="margin: 10px 0; padding: 10px; background-color: #d4edda; border-left: 4px solid #28a745;">
<p><b>A) Low Susceptibility Zones (Z0)</b></p>
<ul style="margin: 5px 0;">
<li>0 &lt; IL ≤ 2 and 2 &lt; Slope% ≤ 5</li>
</ul>
</div>

<div style="margin: 10px 0; padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107;">
<p><b>B) Susceptibility Zones (SZ)</b></p>
<ul style="margin: 5px 0;">
<li>0 &lt; IL ≤ 2 and 5 &lt; Slope% ≤ 15</li>
<li>2 &lt; IL ≤ 5 and 2 &lt; Slope% ≤ 5</li>
<li>5 &lt; IL ≤ 15 and 2 &lt; Slope% ≤ 5</li>
</ul>
</div>

<div style="margin: 10px 0; padding: 10px; background-color: #f8d7da; border-left: 4px solid #dc3545;">
<p><b>C) Respect Zones (RZ)</b></p>
<ul style="margin: 5px 0;">
<li>0 &lt; IL ≤ 2 and Slope% &gt; 15</li>
<li>2 &lt; IL ≤ 5 and Slope% &gt; 5</li>
<li>5 &lt; IL ≤ 15 and Slope% &gt; 5</li>
<li>IL &gt; 15 and Slope% &gt; 2</li>
</ul>
</div>

<p><i>* IL = Liquefaction Index (Iwasaki et al., 1978)</i></p>

<h3>Input Requirements:</h3>
<ul>
<li><b>Digital Terrain Model (DTM):</b> Raster layer representing terrain elevation (DEM/DTM)</li>
<li><b>Liquefaction Index Layer:</b> Polygon vector layer containing IL values from CPT/SPT analysis</li>
<li><b>IL Field:</b> Numeric field containing liquefaction index values (0-100)</li>
<li><b>Apply Styles:</b> Optional - automatically apply predefined visualization styles</li>
</ul>

<h3>Outputs:</h3>
<ul>
<li><b>Slope (%):</b> Raster layer showing terrain slope in percentage</li>
<li><b>Lateral Spreading Zones:</b> Polygon vector layer with classified zones
    <ul>
    <li><i>fid:</i> Feature identifier</li>
    <li><i>code:</i> Numeric zone classification code (101-104: RZ, 201-203: SZ, 300: Z0)</li>
    <li><i>formula:</i> Human-readable classification criteria</li>
    </ul>
</li>
</ul>

<h3>Processing Workflow:</h3>
<ol>
<li>Clip DTM to liquefaction analysis area</li>
<li>Calculate slope percentage from DTM</li>
<li>Convert slope raster to polygons</li>
<li>Intersect slope with liquefaction index layer</li>
<li>Classify areas based on IL and slope thresholds</li>
<li>Merge and organize classified zones</li>
<li>Apply visualization styles (optional)</li>
</ol>

<h3>References:</h3>
<p>
- Italian Seismic Microzonation Guidelines (ICMS, 2008)<br>
- Youd, T. L. (1993). Liquefaction-induced lateral spread displacement<br>
- Youd, T. L., Hansen, C. M., & Bartlett, S. F. (2002). "Revised Multilinear Regression Equations for Prediction of Lateral Spread Displacement"<br>
- Iwasaki, T., et al. (1978). Simplified procedure for assessing soil liquefaction<br>
- Associazione Geotecnica Italiana (AGI). Linee guida per la programmazione ed esecuzione delle indagini geotecniche<br>
- Lancellotta, R. (2012). Geotecnica. (Ed. Zanichelli)
</p>

<p><b>Version:</b> {version}<br>
<b>Author:</b> {author}<br>
<b>Contact:</b> {email}</p>

</body></html>""".format(
            version=__version__,
            author=__author__,
            email='giuseppe.cosentino@cnr.it'
        )
        return self.tr(help_text)

    def tr(self, string: str) -> str:
        """
        Return a translatable string.
        
        Args:
            string: String to translate
            
        Returns:
            Translated string (currently returns input as-is)
        """
        return string

    def createInstance(self) -> 'LateralSpreadingAlgorithm':
        """
        Create a new instance of the algorithm.
        
        Returns:
            New algorithm instance
        """
        return LateralSpreadingAlgorithm()
