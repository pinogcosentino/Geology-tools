# Geology-tools
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18669743.svg)](https://doi.org/10.5281/zenodo.18669743)
![GitHub License](https://img.shields.io/github/license/pinogcosentino/Geology-tools) 
![GitHub Release](https://img.shields.io/github/release/pinogcosentino/Geology-tools)
[![QGIS](https://img.shields.io/badge/QGIS-plugin-orange.svg)](https://plugins.qgis.org/plugins/Geology_tools/)

![Guida](https://github.com/pinogcosentino/Geology-tools/blob/1.0.1/help/source/Geology%20Tools.pdf)

![logo](https://github.com/pinogcosentino/Geology-tools/blob/1.0.1/icon.png)


Geology Tools describes a suite of QGIS plugins designed to streamline geological, hydrological, and seismic microzonation analyses.

# 🪨 Geology Tools — QGIS Plugin

> A suite of QGIS plugins for geological mapping, hydrological analysis, and seismic microzonation.

**Authors:** Giuseppe Cosentino¹ & Francesco Pennica²  

> ¹ Consiglio Nazionale delle Ricerche (CNR) — Istituto di Geoscienze e Georisorse (IGG), Pisa, Italy  
> ² Consiglio Nazionale delle Ricerche (CNR) — Istituto di Geologia Ambientale e Geoingegneria (IGAG), Roma, Italy

---

## 📋 Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Modules](#modules)
  - [1. Geology Mapping — Geology from Points and Lines](#1-geology-mapping--geology-from-points-and-lines)
  - [2. Hydrology — Hydrological Analysis Stream Network (HASN)](#2-hydrology--hydrological-analysis-stream-network-hasn)
  - [3. Seismic Microzonation — Lateral Spreading Analysis (LSA)](#3-seismic-microzonation--lateral-spreading-analysis-lsa)
  - [4. Seismic Microzonation — Seismic Zones with Morphological Gradient (SZMG)](#4-seismic-microzonation--seismic-zones-with-morphological-gradient-szmg)
- [References](#references)
- [License](#license)

---

## Overview

**Geology Tools** is a collection of QGIS plugins designed to streamline geological, hydrological, and seismic microzonation analyses. The plugin integrates QGIS native algorithms with GRASS GIS and SAGA GIS to deliver topologically correct, scientifically robust outputs.

| Module | Description |
|---|---|
| Geology from Points and Lines | Automated geological map generation from vector data |
| HASN | Watershed and stream network extraction from DTM |
| LSA | Lateral spreading susceptibility classification for seismic microzonation |
| SZMG | Detection of steep morphological gradients within seismic zones |

---

## Installation

The plugin is installed directly from the QGIS Plugin Manager:

1. Open QGIS and go to **Plugins → Manage and Install Plugins...**
2. Search for **"Geology"** in the search box.
3. Select **Geology Tools** and click **Install Plugin**.

Once installed, the tools will be available in the **Processing Toolbox** panel.

> ⚠️ The HASN module requires **GRASS GIS** and **SAGA GIS** provider plugins to be installed and active in QGIS.

---

## Modules

---

### 1. Geology Mapping — Geology from Points and Lines

This tool automates the creation of topologically correct geological maps from vector point data (centroids with geological attributes) and linear data (geological boundaries).

#### Workflow

1. **Prepare line data** — Draw geological contact lines that intersect or touch to form closed polygons.
2. **Add point data** — Place one point per polygon with geological attributes (formation codes, lithology, age, etc.).
3. **Run the algorithm** — The tool will automatically:
   - Clean duplicate geometries from points and lines
   - Create polygons from the line network
   - Transfer geological attributes from points to polygons
   - Generate geological contact lines
   - Produce topologically clean outputs

#### Input Parameters

| Parameter | Description |
|---|---|
| **Points with Geological Information** | Point layer with geological attributes; each point should be located within a distinct geological polygon |
| **Geological Attribute Field** | Field containing the primary geological classification (formation code, lithology, etc.) |
| **Line Drawing (Geological Contacts)** | Line layer representing boundaries between geological units; lines should form closed polygons |
| **Vertex Tolerance** | Distance threshold for removing duplicate vertices (default: `0.000001` for decimal degrees) |
| **Spatial Predicate** | Spatial relationship used for joining attributes: `Intersects` (default), `Contains`, `Within`, `Overlaps` |

#### Outputs

| Output | Description |
|---|---|
| **Geological Polygons** | Final polygon layer with geological attributes inherited from points |
| **Geological Contacts** | Line layer representing boundaries between geological units |
| **Clean Points** *(intermediate)* | Point layer after duplicate removal |
| **Intermediate Polygons** *(intermediate)* | Polygons before attribute joining |
| **Line Segments** *(intermediate)* | Individual line segments — useful for QC and troubleshooting |

#### Best Practices

**Line Preparation:**
- Ensure all lines connect properly to form closed polygons; use snapping tools to avoid gaps.
- Lines can overlap to ensure polygon closure.
- Check and fix geometry errors before processing.

**Point Placement:**
- Place exactly **one point per polygon**, well inside the boundary (not near edges).
- Ensure points have valid, non-null attribute values.

**Coordinate Systems:**
- Use projected coordinate systems for accurate topology.
- For geographic coordinates (degrees): `vertex tolerance = 0.000001`
- For projected coordinates (meters): `vertex tolerance = 0.001–0.01`

#### Troubleshooting

| Issue | Solution |
|---|---|
| No polygons created | Check that lines form closed polygons without gaps; verify endpoint snapping |
| Polygons missing attributes | Ensure each polygon has exactly one point inside; try `Intersects` predicate |
| Multiple polygons with same attributes | May be intentional (same unit in multiple areas), or caused by duplicate/misplaced points |

#### Repository & Citation

- 📦 Repository: [https://github.com/pinogcosentino/Geology-from-points-and-lines/tree/1.0](https://github.com/pinogcosentino/Geology-from-points-and-lines/tree/1.0)
- 📄 Zenodo: Cosentino, G. (2025). *QGIS TOOL FOR GEOLOGY FROM POINTS AND LINES (2.0)*. [https://doi.org/10.5281/zenodo.14629465](https://doi.org/10.5281/zenodo.14629465)

---

### 2. Hydrology — Hydrological Analysis Stream Network (HASN)

The HASN module performs comprehensive watershed analysis using an **integrated geoprocessing approach** that synergistically combines **GRASS GIS** and **SAGA GIS** algorithms.

#### Processing Workflow

```
DTM → Fill Sinks → Flow Direction → Flow Accumulation → TWI
                                                      ↓
                                              Stream Delineation
                                                      ↓
                                           Raster → Vector → Smooth
```

**Step 1: Fill Sinks (Wang & Liu Algorithm)**  
Creates a hydrologically correct DTM by filling artificial depressions. The algorithm identifies all sinks, finds the lowest outlet (spill point) on each depression's boundary, and fills it to that elevation.
- **Output:** Filled DTM raster

**Step 2a: Flow Direction**  
Calculates the steepest downslope direction for each cell using the GRASS `r.watershed` algorithm (multi-directional, broader than standard D8).
- **Output:** Drainage direction raster

**Step 2b: Flow Accumulation**  
Calculates the total number of upstream cells draining into each cell, producing a drainage volume map. Used to derive the **Topographic Wetness Index (TWI)**: `TWI = ln(a / tan β)`
- **Output:** TWI raster

> **TWI Interpretation:**
> - **High TWI** → Potential saturation zones (valley bottoms, concavities, foot slopes)
> - **Low TWI** → Dry conditions (steep slopes, ridges)

**Step 2c: Stream Delineation**  
Applies a contributing area threshold (default: 100 m²) to identify river channel cells.
- **Output:** Streams raster

**Step 3: Raster-to-Vector Conversion**  
Converts the stream raster to vector polylines using GRASS `r.to.vect`. The result follows the raster grid (staircase pattern).
- **Output:** LineString vector layer (raw)

**Step 4: Geometry Smoothing**  
Smooths the staircase geometry for cartographic realism. Both the **raw** (for analysis) and **smoothed** (for visualization) versions are retained.
- Parameters: smoothing offset (default: `0.25`), number of iterations
- **Output:** Smoothed stream network vector

#### Best Practices

- Use a high-quality DTM in **projected coordinates** (not geographic).
- Clip the DTM to your study area before processing.
- Start with the default basin size threshold, then adjust:
  - Detailed networks: `25–50 cells`
  - Main channels only: `200–500 cells`
- Validate results against topographic maps or satellite imagery.

#### Limitations

- Flat areas may produce unrealistic flow patterns.
- DTM artifacts can propagate through the analysis.
- Human-modified terrain (roads, dams) may affect results.
- Requires GRASS GIS and SAGA GIS providers to be installed and functional.

#### Applications

Watershed delineation · Stream order classification · Flood hazard mapping · Erosion susceptibility · Hydrological model parameterization · Riparian zone identification · Environmental impact assessment

#### Repository & Citation

- 📦 Repository: [https://github.com/pinogcosentino/Hydrological-Analysis-Stream-Network](https://github.com/pinogcosentino/Hydrological-Analysis-Stream-Network)
- 📄 Zenodo: Cosentino, G. & Pennica, F. (2026). *Hydrological Analysis Stream Network - QGIS Plugin (1.1)*. [https://doi.org/10.5281/zenodo.18254583](https://doi.org/10.5281/zenodo.18254583)

---

### 3. Seismic Microzonation — Lateral Spreading Analysis (LSA)

Lateral spreading refers to the horizontal movement of soil during an earthquake, typically occurring in areas with loose, saturated soils near free faces (riverbanks, sea cliffs). This algorithm classifies terrain susceptibility to lateral spreading based on the **Liquefaction Index (IL)** and **terrain slope percentage**.

#### Input Parameters

| Parameter | Description |
|---|---|
| **Liquefaction Index (IL)** | Polygon vector layer containing IL values from CPT/SPT analysis |
| **Digital Terrain Model (DTM)** | Raster layer representing terrain elevation |

#### Classification Zones

| Zone | Code | Condition |
|---|---|---|
| **Low Susceptibility (Z0)** | 300 | 2 < Slope% ≤ 5 AND 0 < IL ≤ 2 |
| **Susceptibility Zone (SZ)** | 201–203 | 0 < IL ≤ 2 AND 5 < Slope% ≤ 15 · OR · 2 < IL ≤ 5 AND Slope% > 5 · OR · 5 < IL ≤ 15 AND 2 < Slope% ≤ 5 |
| **Respect Zone (RZ)** | 101–104 | 0 < IL ≤ 2 AND Slope% > 15 · OR · 2 < IL ≤ 5 AND Slope% > 5 · OR · 5 < IL ≤ 15 AND Slope% > 5 · OR · IL > 15 AND Slope% > 2 |

#### Processing Workflow

1. Clip DTM to the liquefaction analysis area
2. Calculate slope percentage from DTM
3. Convert slope raster to polygons
4. Intersect slope with liquefaction index layer
5. Classify areas based on IL and slope thresholds
6. Merge and organize classified zones
7. Apply visualization styles (optional)

#### Outputs

| Output | Description |
|---|---|
| **Slope %** | Raster layer showing terrain slope in percentage |
| **Lateral Spreading Zones** | Polygon vector layer with zone classification (`fid`, `code`) |

#### Repository & Citation

- 📦 Repository: [https://github.com/pinogcosentino/Lateral-spreading-for-seismic-microzonation/tree/0.4](https://github.com/pinogcosentino/Lateral-spreading-for-seismic-microzonation/tree/0.4)
- 📄 Zenodo: Cosentino, G. & Pennica, F. (2025). *Lateral spreading for seismic microzonation (0.1)*. [https://doi.org/10.5281/zenodo.14719324](https://doi.org/10.5281/zenodo.14719324)

---

### 4. Seismic Microzonation — Seismic Zones with Morphological Gradient (SZMG)

This algorithm identifies areas with slopes **≥ 15°** within seismic or geological zones. Steep morphological gradients in seismic areas can amplify seismic wave energy and increase the risk of landslides and ground subsidence.

#### Input Parameters

| Parameter | Description |
|---|---|
| **Digital Terrain Model (DTM)** | Elevation raster layer |
| **Geological/Seismic Zones** | Polygon layer defining the study areas |
| **Slope Threshold** | Critical slope angle in degrees (0–90°, default: `15°`) |

#### Processing Workflow

1. **DTM Clipping** — DTM is clipped using the geological vector mask
2. **Slope Calculation** — A slope map is generated in degrees
3. **Threshold Analysis** — Areas exceeding the slope threshold are isolated
4. **Vectorization** — Identified areas are converted to polygons
5. **Attribute Join** — Original seismic zone attributes are preserved

#### Outputs

| Output | Description |
|---|---|
| **Slope Map** | Raster layer showing slope in degrees |
| **High Slope Zones** | Vector polygon layer of areas exceeding the threshold |

#### Repository & Citation

- 📦 Repository: [https://github.com/pinogcosentino/Seismic-Zones-with-morphological-gradient-SMG-](https://github.com/pinogcosentino/Seismic-Zones-with-morphological-gradient-SMG-)
- 📄 Zenodo: Cosentino, G. & Pennica, F. (2025). *Seismic microzones with morphological gradient (0.1)*. [https://doi.org/10.5281/zenodo.14679295](https://doi.org/10.5281/zenodo.14679295)

---

## References

- QGIS Development Team. (2026). *QGIS Geographic Information System* (v3.44). QGIS Association. [https://www.qgis.org](https://www.qgis.org)
- QGIS Plugin Builder: [http://g-sherman.github.io/Qgis-Plugin-Builder/](http://g-sherman.github.io/Qgis-Plugin-Builder/)
- Wang, L., & Liu, H. (2006). An efficient method for identifying and filling surface depressions in digital elevation models.
- Metz, M., et al. (2011). Efficient extraction of drainage networks from massive, radar-based elevation models.
- GRASS Development Team (2023). `r.watershed` module documentation.
- Italian Seismic Microzonation Guidelines (ICMS, 2008).
- Regione Emilia-Romagna, DGR 476/2021 — Indirizzi per gli studi di microzonazione sismica. [Link](https://ambiente.regione.emilia-romagna.it/it/geologia/sismica/indirizzi-per-studi-microzonazione-sismica)
- Youd, T. L. (1993). Liquefaction-induced lateral spread displacement.
- Youd, T. L., Hansen, C. M., & Bartlett, S. F. (2002). Revised Multilinear Regression Equations for Prediction of Lateral Spread Displacement.
- Iwasaki, T., et al. (1978). Simplified procedure for assessing soil liquefaction.
- Lancellotta, R. (2012). *Geotecnica*. Zanichelli.

---

## License

This project is distributed for scientific and educational use. Please cite the authors when using this plugin in publications or projects.
