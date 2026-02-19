# Geology-tools 
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18669743.svg)](https://doi.org/10.5281/zenodo.18669743)![GitHub License](https://img.shields.io/github/license/pinogcosentino/Geology-tools) ![GitHub Release](https://img.shields.io/github/v/release/pinogcosentino/Geology-tools/releases/tag/1.0))


Geology Tools describes a suite of QGIS plugins designed to streamline geological, hydrological, and seismic microzonation analyses.

The following is a summary of the main modules and their functionalities:

Geology Mapping
The Geology from points and lines tool automates the creation of geological maps.
- Workflow: The user draws geological contact lines to form closed polygons and places points with geological attributes (formation codes, lithology, etc.) inside them.
- Automation: The algorithm cleans duplicate geometries, creates polygons from the line network, and transfers the attributes from the points to the resulting polygons.
- Output: Produces topologically clean geological polygons and contact lines ready for GIS analysis.

Hydrology
The Hydrological Analysis Stream Network (HASN) module utilizes an integrated approach, leveraging GRASS GIS and SAGA GIS algorithms for robust watershed analysis.
- Terrain Correction: It uses the Wang & Liu algorithm to fill sinks in Digital Terrain Models (DTM), ensuring a hydrologically correct surface.
- Flow & Indices: It calculates drainage directions and flow accumulation to derive the Topographic Wetness Index (TWI), which identifies areas prone to saturation and runoff
- Stream Delineation: The tool generates a vector stream network from the DTM, offering both a raw version for analysis and a "smooth" version for better cartographic visualization.

Seismic Microzonation
This section includes tools for evaluating ground stability and seismic risk:
- Lateral Spreading Analysis (LSA): Identifies horizontal soil movement risks during earthquakes by crossing the Liquefaction Index (IL)with terrain slope percentages. It classifies areas into Respect Zones (RZ), Susceptibility Zones (SZ), or Low Susceptibility Zones (Z0).
- Seismic Zones with Morphological Gradient (SZMG): Identifies areas with slopes > 15° within seismic zones. This is critical because steep morphological gradients can amplify seismic waves and increase the risk of seismic-caused landslides.

<img width="646" height="624" alt="icon" src="https://github.com/user-attachments/assets/4203baa4-161c-49e1-9410-afc598e6f42a" />
