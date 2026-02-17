
# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   Hydrological Analysis Streams - QGIS Processing Algorithm             *
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

from typing import Dict, Any, Optional
from dataclasses import dataclass

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorDestination,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsRasterLayer,
    QgsMessageLog,
    Qgis
)
import processing


@dataclass
class HydrologicalParameters:
    """
    Data class for hydrological analysis parameters.
    
    Attributes:
        min_slope: Minimum slope in degrees for fill sinks algorithm
        min_basin_size: Minimum basin size in cells for stream delineation
        iterations: Number of smoothing iterations
        max_angle: Maximum vertex angle for smoothing in degrees
        offset: Smoothing offset value (0.0-1.0)
    """
    min_slope: float
    min_basin_size: int
    iterations: int
    max_angle: int
    offset: float
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate parameter ranges.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not 0.01 <= self.min_slope <= 90:
            return False, f"Minimum slope must be between 0.01 and 90 degrees (got {self.min_slope})"
        
        if self.min_basin_size < 1:
            return False, f"Minimum basin size must be >= 1 (got {self.min_basin_size})"
        
        if not 1 <= self.iterations <= 10:
            return False, f"Iterations must be between 1 and 10 (got {self.iterations})"
        
        if not 0 <= self.max_angle <= 360:
            return False, f"Maximum angle must be between 0 and 360 degrees (got {self.max_angle})"
        
        if not 0.01 <= self.offset <= 1.0:
            return False, f"Offset must be between 0.01 and 1.0 (got {self.offset})"
        
        return True, ""


class HydrologicalAnalysisStreams(QgsProcessingAlgorithm):
    """
    QGIS Processing Algorithm for comprehensive hydrological stream network analysis.
    
    This algorithm performs a complete hydrological analysis workflow on a Digital
    Terrain Model (DTM) to extract drainage networks and hydrological features.
    
    The analysis includes:
    1. Depression filling using Wang & Liu algorithm
    2. Flow direction and accumulation calculation
    3. Stream network delineation
    4. Topographic indices computation
    5. Vector stream network extraction and smoothing
    
    Output products:
    - Filled DTM (depressions removed)
    - Drainage direction raster
    - Stream network (raster and vector)
    - Half-basin delineation
    - Topographic Convergence Index (TCI)
    - Smoothed vector stream network
    
    Applications:
    - Watershed delineation
    - Flood risk assessment
    - Erosion modeling
    - Hydrological modeling
    - Environmental impact assessment
    """
    
    # Input parameter names
    INPUT_DTM = 'digital_terrain_model_dtm'
    MIN_SLOPE = 'minimum_slope_degree'
    MIN_BASIN_SIZE = 'minimum_size_of_exterior_watershed_basin'
    ITERATIONS = 'smoothing_iterations'
    MAX_ANGLE = 'maximum_node_corner_vertex_angle'
    OFFSET = 'smoothing_offset'
    
    # Output parameter names
    OUTPUT_VECTOR_RAW = 'vector_stream_raw'
    OUTPUT_SMOOTH = 'smoothed_streams'
    OUTPUT_FILLED_DTM = 'filled_dtm_wang_liu'
    OUTPUT_STREAM = 'stream_network_raster'
    OUTPUT_DRAINAGE = 'drainage_direction'
    OUTPUT_HALF_BASIN = 'half_basin'
    OUTPUT_TCI = 'topographic_index_ln_a_tan_b'
    
    # Processing constants
    DEFAULT_MIN_SLOPE = 0.1
    DEFAULT_MIN_BASIN_SIZE = 100
    DEFAULT_ITERATIONS = 1
    DEFAULT_MAX_ANGLE = 180
    DEFAULT_OFFSET = 0.25
    GRASS_MEMORY = 300
    GRASS_CONVERGENCE = 5
    TOTAL_STEPS = 4

    def __init__(self):
        """Initialize the algorithm."""
        super().__init__()

    # ========================================================================
    # Translation and Metadata Methods
    # ========================================================================
    
    def tr(self, string: str) -> str:
        """
        Return a translatable string.
        
        Args:
            string: String to translate
            
        Returns:
            Translated string
        """
        return QCoreApplication.translate('Processing', string)

    def name(self) -> str:
        """Return internal algorithm name."""
        return 'hydrological_analysis_stream_network'

    def displayName(self) -> str:
        """Return user-friendly algorithm name."""
        return self.tr('Hydrological Analysis - Stream Network (HASN)')

    def group(self) -> str:
        """Return algorithm group."""
        return self.tr('Hydrology')

    def groupId(self) -> str:
        """Return internal group ID."""
        return 'hydrology'

    def shortHelpString(self) -> str:
        """Return algorithm help documentation."""
        return self.tr("""<html><body>
<h2>Drainage Network Extraction from Digital Terrain Models</h2>

<p>This algorithm performs a comprehensive hydrological analysis on a Digital Terrain Model (DTM)
to extract drainage networks and compute hydrological indices.</p>

<h3>Workflow Overview:</h3>
<ol>
<li><b>Depression Filling:</b> Removes sinks and depressions using Wang & Liu (2006) algorithm</li>
<li><b>Flow Analysis:</b> Computes flow directions and accumulation using r.watershed</li>
<li><b>Stream Delineation:</b> Extracts stream network based on flow accumulation threshold</li>
<li><b>Vectorization:</b> Converts raster streams to vector format</li>
<li><b>Smoothing:</b> Applies geometric smoothing for cartographic quality</li>
</ol>

<h3>Input Parameters:</h3>

<p><b>Digital Terrain Model (DTM):</b></p>
<ul>
<li>Single-band raster representing terrain elevation</li>
<li>Should be in a projected coordinate system for accurate analysis</li>
<li>Higher resolution DTMs produce more detailed stream networks</li>
<li>Recommended: Remove data artifacts before processing</li>
</ul>

<p><b>Minimum Slope (degrees):</b></p>
<ul>
<li>Minimum slope used in depression filling algorithm</li>
<li>Range: 0.01° - 90°</li>
<li>Default: 0.1°</li>
<li>Lower values preserve more terrain detail</li>
<li>Higher values create more aggressive filling</li>
</ul>

<p><b>Minimum Basin Size (cells):</b></p>
<ul>
<li>Threshold for stream initiation in number of cells</li>
<li>Minimum: 1 cell</li>
<li>Default: 100 cells</li>
<li>Lower values create denser stream networks</li>
<li>Higher values extract only major streams</li>
<li>Typical ranges: 50-500 cells depending on resolution</li>
</ul>

<p><b>Smoothing Iterations:</b></p>
<ul>
<li>Number of smoothing passes applied to vector streams</li>
<li>Range: 1-10 iterations</li>
<li>Default: 1 iteration</li>
<li>More iterations = smoother but less accurate geometries</li>
</ul>

<p><b>Maximum Vertex Angle (degrees):</b></p>
<ul>
<li>Maximum angle for vertex preservation during smoothing</li>
<li>Range: 0° - 360°</li>
<li>Default: 180°</li>
<li>Lower values preserve sharp bends</li>
<li>180° allows all vertices to be smoothed</li>
</ul>

<p><b>Smoothing Offset:</b></p>
<ul>
<li>Distance offset for smoothing algorithm</li>
<li>Range: 0.01 - 1.0</li>
<li>Default: 0.25</li>
<li>Controls the degree of displacement during smoothing</li>
</ul>

<h3>Output Products:</h3>

<p><b>Primary Outputs:</b></p>
<ul>
<li><b>Filled DTM:</b> Depression-filled elevation model (raster)</li>
<li><b>Raw Stream Network:</b> Initial vector stream network without smoothing</li>
<li><b>Smoothed Stream Network:</b> Cartographically enhanced stream lines (vector)</li>
</ul>

<p><b>Optional Hydrological Outputs:</b></p>
<ul>
<li><b>Stream Network (Raster):</b> Binary raster of stream cells</li>
<li><b>Drainage Directions:</b> Flow direction for each cell (D8 algorithm)</li>
<li><b>Half Basins:</b> Sub-watershed delineation</li>
<li><b>Topographic Index:</b> ln(a/tan(β)) - wetness index for each cell</li>
</ul>

<h3>Technical Details:</h3>

<p><b>Depression Filling Algorithm:</b></p>
<ul>
<li>Uses Wang & Liu (2006) method</li>
<li>Preserves terrain characteristics better than traditional filling</li>
<li>Enforces minimum slope to ensure drainage</li>
</ul>

<p><b>Flow Analysis:</b></p>
<ul>
<li>GRASS GIS r.watershed module</li>
<li>Multiple Flow Direction (MFD) algorithm available</li>
<li>Computes flow accumulation, direction, and derived indices</li>
</ul>

<p><b>Topographic Convergence Index (TCI):</b></p>
<ul>
<li>Also known as Topographic Wetness Index (TWI)</li>
<li>Formula: ln(a/tan(β))</li>
<li>Where: a = specific catchment area, β = slope angle</li>
<li>Indicates areas prone to saturation</li>
</ul>

<h3>Best Practices:</h3>

<p><b>Input Data Preparation:</b></p>
<ul>
<li>Use high-quality DTM with minimal artifacts</li>
<li>Ensure DTM is in projected coordinates (not geographic)</li>
<li>Remove or interpolate NoData values if present</li>
<li>Consider pre-processing with Gaussian filter for noisy data</li>
</ul>

<p><b>Parameter Selection:</b></p>
<ul>
<li>Start with default minimum basin size, adjust based on results</li>
<li>For detailed networks: use lower threshold (25-50 cells)</li>
<li>For main channels only: use higher threshold (200-500 cells)</li>
<li>Consider DTM resolution when setting basin size</li>
</ul>

<p><b>Quality Control:</b></p>
<ul>
<li>Visually inspect filled DTM for artifacts</li>
<li>Compare stream network with topographic maps or imagery</li>
<li>Check for unrealistic stream patterns</li>
<li>Validate drainage directions in complex terrain</li>
</ul>

<p><b>Performance Optimization:</b></p>
<ul>
<li>Clip DTM to study area before processing</li>
<li>Consider resampling very high-resolution DTMs</li>
<li>Processing time increases with DTM size</li>
<li>GRASS algorithms may require significant memory</li>
</ul>

<h3>Limitations and Considerations:</h3>
<ul>
<li>Flat areas may produce unrealistic flow patterns</li>
<li>DTM artifacts can propagate through the analysis</li>
<li>Stream extraction is sensitive to basin size threshold</li>
<li>Human-modified terrain (roads, dams) may affect results</li>
<li>Requires GRASS GIS plugin to be installed and functional</li>
</ul>

<h3>Applications:</h3>
<ul>
<li>Watershed and sub-watershed delineation</li>
<li>Stream order classification (Strahler, Shreve)</li>
<li>Flood hazard mapping</li>
<li>Erosion susceptibility assessment</li>
<li>Hydrological model parameterization</li>
<li>Riparian zone identification</li>
<li>Environmental impact assessment</li>
</ul>

<h3>References:</h3>
<p>
- Wang, L., & Liu, H. (2006). An efficient method for identifying and filling surface depressions in digital elevation models.<br>
- Metz, M., et al. (2011). Efficient extraction of drainage networks from massive, radar-based elevation models.<br>
- GRASS Development Team (2023). r.watershed module documentation.
</p>

<p><b>Author:</b> {author}<br>
<b>Email:</b> {email}<br>
<b>Version:</b> {version}</p>

</body></html>""".format(
            author=__author__,
            email='giuseppe.cosentino@cnr.it',
            version=__version__
        ))

    def createInstance(self) -> 'HydrologicalAnalysisStreams':
        """
        Create a new instance of the algorithm.
        
        Returns:
            New algorithm instance
        """
        return HydrologicalAnalysisStreams()

    # ========================================================================
    # Parameter Initialization
    # ========================================================================
    
    def initAlgorithm(self, config: Optional[Dict] = None) -> None:
        """
        Define inputs and outputs of the algorithm.
        
        Args:
            config: Optional configuration dictionary
        """
        # Main input: DTM
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DTM,
                self.tr('Digital Terrain Model (DTM)'),
                defaultValue=None
            )
        )
        
        # Processing parameters
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_SLOPE,
                self.tr('Minimum Slope (degrees)'),
                type=QgsProcessingParameterNumber.Double,
                minValue=0.01,
                maxValue=90,
                defaultValue=self.DEFAULT_MIN_SLOPE
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_BASIN_SIZE,
                self.tr('Minimum Basin Size (cells)'),
                type=QgsProcessingParameterNumber.Integer,
                minValue=1,
                defaultValue=self.DEFAULT_MIN_BASIN_SIZE
            )
        )
        
        # Smoothing parameters
        self.addParameter(
            QgsProcessingParameterNumber(
                self.ITERATIONS,
                self.tr('Smoothing Iterations'),
                type=QgsProcessingParameterNumber.Integer,
                minValue=1,
                maxValue=10,
                defaultValue=self.DEFAULT_ITERATIONS
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_ANGLE,
                self.tr('Maximum Vertex Angle (degrees)'),
                type=QgsProcessingParameterNumber.Integer,
                minValue=0,
                maxValue=360,
                defaultValue=self.DEFAULT_MAX_ANGLE
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.OFFSET,
                self.tr('Smoothing Offset'),
                type=QgsProcessingParameterNumber.Double,
                minValue=0.01,
                maxValue=1.0,
                defaultValue=self.DEFAULT_OFFSET
            )
        )
        
        # Primary outputs
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_FILLED_DTM,
                self.tr('Filled DTM (Wang & Liu)'),
                createByDefault=True,
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT_VECTOR_RAW,
                self.tr('Raw Stream Network (Vector)'),
                type=QgsProcessing.TypeVectorLine,
                createByDefault=True,
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_SMOOTH,
                self.tr('Smoothed Stream Network'),
                type=QgsProcessing.TypeVectorLine,
                createByDefault=True,
                defaultValue=None
            )
        )
        
        # Optional hydrological outputs
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_STREAM,
                self.tr('Stream Network (Raster)'),
                optional=True,
                createByDefault=True,
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_DRAINAGE,
                self.tr('Drainage Directions'),
                optional=True,
                createByDefault=True,
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_HALF_BASIN,
                self.tr('Half Basins'),
                optional=True,
                createByDefault=True,
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_TCI,
                self.tr('Topographic Convergence Index ln(a/tan(β))'),
                optional=True,
                createByDefault=True,
                defaultValue=None
            )
        )

    # ========================================================================
    # Input Validation
    # ========================================================================
    
    def checkParameterValues(
        self, 
        parameters: Dict[str, Any], 
        context: Any
    ) -> tuple[bool, str]:
        """
        Validate parameters before processing starts.
        
        Args:
            parameters: Dictionary of input parameters
            context: Processing context
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate DTM
        dtm = self.parameterAsRasterLayer(parameters, self.INPUT_DTM, context)
        if dtm is None:
            return False, self.tr('Invalid DTM raster layer')
        
        if not dtm.isValid():
            return False, self.tr('DTM raster layer is not valid')
        
        # Check if DTM has data
        if dtm.extent().isEmpty():
            return False, self.tr('DTM has empty extent')
        
        # Validate parameters using dataclass
        hydro_params = HydrologicalParameters(
            min_slope=self.parameterAsDouble(parameters, self.MIN_SLOPE, context),
            min_basin_size=self.parameterAsInt(parameters, self.MIN_BASIN_SIZE, context),
            iterations=self.parameterAsInt(parameters, self.ITERATIONS, context),
            max_angle=self.parameterAsInt(parameters, self.MAX_ANGLE, context),
            offset=self.parameterAsDouble(parameters, self.OFFSET, context)
        )
        
        is_valid, error_msg = hydro_params.validate()
        if not is_valid:
            return False, self.tr(error_msg)
        
        return super().checkParameterValues(parameters, context)

    # ========================================================================
    # Main Processing Algorithm
    # ========================================================================
    
    def processAlgorithm(
        self, 
        parameters: Dict[str, Any], 
        context: Any, 
        model_feedback: Any
    ) -> Dict[str, Any]:
        """
        Execute the hydrological analysis algorithm.
        
        Args:
            parameters: Dictionary of input parameters
            context: Processing context
            model_feedback: Feedback object for progress reporting
            
        Returns:
            Dictionary containing output results
            
        Raises:
            QgsProcessingException: If processing fails at any step
        """
        # Initialize multi-step feedback
        feedback = QgsProcessingMultiStepFeedback(self.TOTAL_STEPS, model_feedback)
        results = {}
        outputs = {}
        
        try:
            # Get input parameters
            dtm = self.parameterAsRasterLayer(parameters, self.INPUT_DTM, context)
            hydro_params = HydrologicalParameters(
                min_slope=self.parameterAsDouble(parameters, self.MIN_SLOPE, context),
                min_basin_size=self.parameterAsInt(parameters, self.MIN_BASIN_SIZE, context),
                iterations=self.parameterAsInt(parameters, self.ITERATIONS, context),
                max_angle=self.parameterAsInt(parameters, self.MAX_ANGLE, context),
                offset=self.parameterAsDouble(parameters, self.OFFSET, context)
            )
            
            # Print processing information
            feedback.pushInfo(self.tr('=' * 60))
            feedback.pushInfo(self.tr('Starting Hydrological Stream Network Analysis'))
            feedback.pushInfo(self.tr('=' * 60))
            feedback.pushInfo(self.tr(f'DTM: {dtm.name()}'))
            feedback.pushInfo(self.tr(f'Resolution: {dtm.rasterUnitsPerPixelX():.2f} x {dtm.rasterUnitsPerPixelY():.2f}'))
            feedback.pushInfo(self.tr(f'Extent: {dtm.extent().toString()}'))
            feedback.pushInfo(self.tr(f'Minimum slope: {hydro_params.min_slope}°'))
            feedback.pushInfo(self.tr(f'Basin size threshold: {hydro_params.min_basin_size} cells'))
            feedback.pushInfo('')
            
            # Step 1: Fill sinks
            feedback.pushInfo(self.tr('Step 1/{}: Filling DTM depressions (Wang & Liu algorithm)...').format(
                self.TOTAL_STEPS
            ))
            outputs['filled_dtm'] = self._fill_sinks_wang_liu(
                parameters, hydro_params, context, feedback
            )
            results[self.OUTPUT_FILLED_DTM] = outputs['filled_dtm']
            
            feedback.setCurrentStep(1)
            if feedback.isCanceled():
                return {}
            
            # Step 2: Flow analysis
            feedback.pushInfo(self.tr('Step 2/{}: Computing flow directions and stream network...').format(
                self.TOTAL_STEPS
            ))
            watershed_outputs = self._run_watershed_analysis(
                outputs['filled_dtm'], hydro_params, parameters, context, feedback
            )
            outputs.update(watershed_outputs)
            
            # Store watershed results
            results[self.OUTPUT_STREAM] = watershed_outputs.get('stream')
            results[self.OUTPUT_DRAINAGE] = watershed_outputs.get('drainage')
            results[self.OUTPUT_HALF_BASIN] = watershed_outputs.get('half_basin')
            results[self.OUTPUT_TCI] = watershed_outputs.get('tci')
            
            feedback.setCurrentStep(2)
            if feedback.isCanceled():
                return {}
            
            # Validate that streams were generated
            if not watershed_outputs.get('stream'):
                raise QgsProcessingException(
                    self.tr('No stream network generated. Try reducing minimum basin size.')
                )
            
            # Step 3: Raster to vector conversion
            feedback.pushInfo(self.tr('Step 3/{}: Converting stream network to vector format...').format(
                self.TOTAL_STEPS
            ))
            outputs['vector_raw'] = self._raster_to_vector(
                watershed_outputs['stream'], parameters, context, feedback
            )
            results[self.OUTPUT_VECTOR_RAW] = outputs['vector_raw']
            
            feedback.setCurrentStep(3)
            if feedback.isCanceled():
                return {}
            
            # Step 4: Geometry smoothing
            feedback.pushInfo(self.tr('Step 4/{}: Smoothing stream network geometry...').format(
                self.TOTAL_STEPS
            ))
            outputs['smoothed'] = self._smooth_geometry(
                outputs['vector_raw'], hydro_params, parameters, context, feedback
            )
            results[self.OUTPUT_SMOOTH] = outputs['smoothed']
            
            # Processing complete
            feedback.pushInfo('')
            feedback.pushInfo(self.tr('=' * 60))
            feedback.pushInfo(self.tr('✓ Hydrological analysis completed successfully!'))
            feedback.pushInfo(self.tr('=' * 60))
            self._print_summary(results, context, feedback)
            
            return results
            
        except QgsProcessingException:
            raise
        except Exception as e:
            error_msg = self.tr(f'Unexpected error during hydrological analysis: {str(e)}')
            self._log_error(error_msg)
            raise QgsProcessingException(error_msg)

    # ========================================================================
    # Helper Methods for Processing Steps
    # ========================================================================
    
    def _fill_sinks_wang_liu(
        self,
        parameters: Dict[str, Any],
        hydro_params: HydrologicalParameters,
        context: Any,
        feedback: Any
    ) -> str:
        """
        Fill depressions in DTM using Wang & Liu algorithm.
        
        Args:
            parameters: Algorithm parameters
            hydro_params: Hydrological parameters
            context: Processing context
            feedback: Feedback object
            
        Returns:
            Path to filled DTM
            
        Raises:
            QgsProcessingException: If fill sinks fails
        """
        alg_params = {
            'BAND': 1,
            'INPUT': parameters[self.INPUT_DTM],
            'MIN_SLOPE': hydro_params.min_slope,
            'CREATION_OPTIONS': None,
            'OUTPUT_FILLED_DEM': parameters[self.OUTPUT_FILLED_DTM]
        }
        
        try:
            result = processing.run(
                'native:fillsinkswangliu',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            if not result or 'OUTPUT_FILLED_DEM' not in result:
                raise QgsProcessingException(
                    self.tr('Fill sinks algorithm did not produce valid output')
                )
            
            return result['OUTPUT_FILLED_DEM']
            
        except Exception as e:
            raise QgsProcessingException(
                self.tr(f'Error in depression filling: {str(e)}')
            )
    
    def _run_watershed_analysis(
        self,
        filled_dtm: str,
        hydro_params: HydrologicalParameters,
        parameters: Dict[str, Any],
        context: Any,
        feedback: Any
    ) -> Dict[str, Any]:
        """
        Run GRASS r.watershed for flow analysis and stream delineation.
        
        Args:
            filled_dtm: Path to filled DTM
            hydro_params: Hydrological parameters
            parameters: Algorithm parameters
            context: Processing context
            feedback: Feedback object
            
        Returns:
            Dictionary with watershed outputs
            
        Raises:
            QgsProcessingException: If watershed analysis fails
        """
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
            'convergence': self.GRASS_CONVERGENCE,
            'depression': None,
            'disturbed_land': None,
            'elevation': filled_dtm,
            'flow': None,
            'max_slope_length': None,
            'memory': self.GRASS_MEMORY,
            'threshold': hydro_params.min_basin_size,
            'drainage': parameters[self.OUTPUT_DRAINAGE],
            'half_basin': parameters[self.OUTPUT_HALF_BASIN],
            'stream': parameters[self.OUTPUT_STREAM],
            'tci': parameters[self.OUTPUT_TCI]
        }
        
        try:
            result = processing.run(
                'grass:r.watershed',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            return {
                'stream': result.get('stream'),
                'drainage': result.get('drainage'),
                'half_basin': result.get('half_basin'),
                'tci': result.get('tci')
            }
            
        except Exception as e:
            raise QgsProcessingException(
                self.tr(f'Error in watershed analysis: {str(e)}. '
                       'Ensure GRASS GIS plugin is properly installed.')
            )
    
    def _raster_to_vector(
        self,
        stream_raster: str,
        parameters: Dict[str, Any],
        context: Any,
        feedback: Any
    ) -> str:
        """
        Convert raster stream network to vector lines.
        
        Args:
            stream_raster: Path to stream raster
            parameters: Algorithm parameters
            context: Processing context
            feedback: Feedback object
            
        Returns:
            Path to vector stream network
            
        Raises:
            QgsProcessingException: If conversion fails
        """
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
            'input': stream_raster,
            'type': 0,  # line
            'output': parameters[self.OUTPUT_VECTOR_RAW]
        }
        
        try:
            result = processing.run(
                'grass:r.to.vect',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            return result['output']
            
        except Exception as e:
            raise QgsProcessingException(
                self.tr(f'Error converting raster to vector: {str(e)}')
            )
    
    def _smooth_geometry(
        self,
        vector_streams: str,
        hydro_params: HydrologicalParameters,
        parameters: Dict[str, Any],
        context: Any,
        feedback: Any
    ) -> str:
        """
        Smooth vector stream geometry for cartographic quality.
        
        Args:
            vector_streams: Path to vector streams
            hydro_params: Hydrological parameters
            parameters: Algorithm parameters
            context: Processing context
            feedback: Feedback object
            
        Returns:
            Path to smoothed vector streams
            
        Raises:
            QgsProcessingException: If smoothing fails
        """
        alg_params = {
            'INPUT': vector_streams,
            'ITERATIONS': hydro_params.iterations,
            'MAX_ANGLE': hydro_params.max_angle,
            'OFFSET': hydro_params.offset,
            'OUTPUT': parameters[self.OUTPUT_SMOOTH]
        }
        
        try:
            result = processing.run(
                'native:smoothgeometry',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            return result['OUTPUT']
            
        except Exception as e:
            raise QgsProcessingException(
                self.tr(f'Error smoothing geometry: {str(e)}')
            )

    # ========================================================================
    # Reporting and Logging Methods
    # ========================================================================
    
    def _print_summary(
        self, 
        results: Dict[str, Any], 
        context: Any, 
        feedback: Any
    ) -> None:
        """
        Print processing summary.
        
        Args:
            results: Processing results dictionary
            context: Processing context
            feedback: Feedback object
        """
        try:
            feedback.pushInfo(self.tr('Output Summary:'))
            
            # Count outputs
            raster_outputs = []
            vector_outputs = []
            
            for output_name, output_path in results.items():
                if output_path:
                    if 'dtm' in output_name.lower() or 'raster' in output_name.lower() or \
                       'drainage' in output_name.lower() or 'basin' in output_name.lower() or \
                       'tci' in output_name.lower():
                        raster_outputs.append(output_name)
                    else:
                        vector_outputs.append(output_name)
            
            if raster_outputs:
                feedback.pushInfo(self.tr(f'  Raster outputs: {len(raster_outputs)}'))
                for name in raster_outputs:
                    feedback.pushInfo(self.tr(f'    - {name}'))
            
            if vector_outputs:
                feedback.pushInfo(self.tr(f'  Vector outputs: {len(vector_outputs)}'))
                for name in vector_outputs:
                    feedback.pushInfo(self.tr(f'    - {name}'))
                    
        except Exception as e:
            feedback.pushWarning(
                self.tr(f'Could not generate summary: {str(e)}')
            )

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
