# 🔥 Fire-Prone Vegetation Analysis using Google Earth Engine

A Python tool for analyzing vegetation characteristics and assessing fire risk using satellite imagery from Google Earth Engine (Sentinel-2 and Landsat 8/9).

![Fire Risk Analysis](https://img.shields.io/badge/Python-3.11%2B-blue)
![Earth Engine](https://img.shields.io/badge/Google-Earth%20Engine-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Google Earth Engine Setup](#google-earth-engine-setup)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Output](#output)
- [Examples](#examples)
- [Contributing](#contributing)

---

## ✨ Features

### Vegetation Indices
- **NDVI** (Normalized Difference Vegetation Index) - Vegetation health
- **SAVI** (Soil Adjusted Vegetation Index) - Accounts for soil brightness
- **EVI** (Enhanced Vegetation Index) - Better for high biomass areas
- **NDMI** (Normalized Difference Moisture Index) - Vegetation water content
- **NBR** (Normalized Burn Ratio) - Burn severity assessment

### Fire Risk Assessment
- **Plant Color Analysis** - Greenness, redness, and stress indicators
- **Soil Characteristics** - Bare soil index and moisture content
- **Vegetation Diversity** - Texture analysis for mixed vegetation types
- **Comprehensive Fire Risk Score** (0-100 scale)
- **5-Level Risk Classification** (Very Low, Low, Moderate, High, Very High)

### Visualization
- Interactive HTML maps with layer controls
- Static matplotlib visualizations
- Statistical reports with area calculations
- Export to Google Drive for large areas

---

## 📦 Requirements

### Software
- **Python 3.11 or higher**
- **Google Account** with Earth Engine access
- **Internet connection** for downloading satellite data

### Python Packages
- `earthengine-api` - Google Earth Engine API
- `geemap` - Interactive mapping with Earth Engine
- `folium` - HTML map generation
- `matplotlib` - Static visualizations
- `numpy<2` - Numerical computing (version 1.x required)
- `pandas` - Data analysis
- `seaborn` - Statistical visualizations
- `scipy` - Scientific computing

---

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/fire-risk-analysis.git
cd fire-risk-analysis
```

### Step 2: Create Virtual Environment (Recommended)

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install earthengine-api geemap folium matplotlib "numpy<2" pandas seaborn scipy
```

---

## 🌍 Google Earth Engine Setup

### 1. Sign Up for Earth Engine Access

1. Go to: **https://earthengine.google.com/signup/**
2. Sign in with your Google account
3. Fill out the registration form
4. Wait for approval (usually instant to a few hours)

### 2. Authenticate Earth Engine

**After installation, authenticate once:**

```bash
python3 -c "import ee; ee.Authenticate()"
```

This will:
- Open your browser
- Ask you to sign in with Google
- Save credentials for future use

**Test if authentication worked:**
```bash
python3 -c "import ee; ee.Initialize(); print('✅ Earth Engine is ready!')"
```

---

## 🔧 Troubleshooting Common Issues

### Issue 1: "No module named 'ee'"

**Solution:**
```bash
# Make sure you're using the correct Python
which python3
python3 -m pip install earthengine-api
```

### Issue 2: SSL Certificate Error (Mac)

**Solution:**
```bash
# Install SSL certificates
/Applications/Python\ 3.12/Install\ Certificates.command

# Or add this to the top of your script:
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

### Issue 3: NumPy Version Conflict

**Error:** `numpy.core._multiarray_umath failed to import`

**Solution:**
```bash
pip uninstall numpy
pip install "numpy<2"
```

### Issue 4: Multiple Python Versions

**Solution:**
Always use `python3 -m pip` instead of just `pip`:
```bash
python3 -m pip install earthengine-api
```

### Issue 5: "Earth Engine not initialized"

**Solution:**
```bash
# Re-authenticate
python3 -c "import ee; ee.Authenticate(); ee.Initialize()"
```

---

## 📖 Usage

### Basic Usage

```python
from fire_vegetation_analysis import GEEFireRiskAnalyzer

# Define area of interest (California example)
area = [-118.7, 34.0, -118.5, 34.2]  # [lon_min, lat_min, lon_max, lat_max]

# Create analyzer
analyzer = GEEFireRiskAnalyzer(
    area_of_interest=area,
    start_date='2024-06-01',
    end_date='2024-09-30',
    satellite='sentinel2'  # or 'landsat8' or 'landsat9'
)

# Generate statistics report
analyzer.generate_statistics_report()

# Create interactive map
map_obj = analyzer.visualize_interactive_map()
map_obj.save('fire_risk_map.html')

# Download data for local analysis (small areas only)
data = analyzer.download_data_for_local_analysis(scale=30)
analyzer.visualize_local_analysis(data)
```

### Analyze Custom Location

```python
# Analyze specific coordinates with buffer
analyzer = example_custom_location(
    lon=-118.6,  # Longitude
    lat=34.1,    # Latitude
    buffer_km=10  # Analysis radius in kilometers
)
```

### Export Large Areas to Google Drive

```python
# For areas too large to download directly
analyzer.export_to_drive(
    description='my_fire_risk_analysis',
    scale=30  # Resolution in meters
)
# Check progress at: https://code.earthengine.google.com/tasks
```

---

## 📊 Output

### 1. Interactive HTML Map
- **File:** `fire_risk_map.html`
- Multiple layers: True color, NDVI, NDMI, Fire Risk Score, Risk Classification
- Layer controls for toggling visibility
- Zoom and pan functionality

### 2. Static Visualization
- **File:** `fire_risk_analysis_gee.png`
- 3x3 grid showing all analysis layers
- NDVI, SAVI, EVI, NDMI, Plant color, Soil characteristics, Diversity, Risk score, Risk classification

### 3. Statistics Report
Printed to console with:
- Vegetation index statistics (mean, std, range)
- Fire risk distribution by category
- Area calculations (km²) for each risk level
- Overall risk assessment and recommendations

---

## 🌟 Examples

### Example 1: California Wildfire Area

```python
# Santa Monica Mountains, CA (fire-prone area)
california_aoi = [-118.7, 34.0, -118.5, 34.2]

analyzer = GEEFireRiskAnalyzer(
    area_of_interest=california_aoi,
    start_date='2024-06-01',
    end_date='2024-09-30',
    satellite='sentinel2'
)

analyzer.generate_statistics_report()
map_obj = analyzer.visualize_interactive_map()
map_obj.save('california_fire_risk.html')
```

### Example 2: Custom Point Location

```python
# Analyze any location by coordinates
def analyze_location(lon, lat, radius_km=5):
    point = ee.Geometry.Point([lon, lat])
    aoi = point.buffer(radius_km * 1000)
    
    analyzer = GEEFireRiskAnalyzer(
        area_of_interest=aoi,
        start_date='2024-06-01',
        end_date='2024-09-30',
        satellite='sentinel2'
    )
    
    analyzer.generate_statistics_report()
    return analyzer

# Example: Yosemite National Park
analyzer = analyze_location(lon=-119.5383, lat=37.8651, radius_km=10)
```

### Example 3: Time Series Analysis

```python
# Compare fire risk across different seasons
import datetime

def seasonal_analysis(aoi, year=2024):
    seasons = {
        'Spring': (f'{year}-03-01', f'{year}-05-31'),
        'Summer': (f'{year}-06-01', f'{year}-08-31'),
        'Fall': (f'{year}-09-01', f'{year}-11-30'),
        'Winter': (f'{year-1}-12-01', f'{year}-02-28')
    }
    
    results = {}
    for season, (start, end) in seasons.items():
        analyzer = GEEFireRiskAnalyzer(aoi, start, end, 'sentinel2')
        print(f"\n{'='*50}\n{season} Analysis\n{'='*50}")
        analyzer.generate_statistics_report()
        results[season] = analyzer
    
    return results

# Run seasonal analysis
aoi = [-118.7, 34.0, -118.5, 34.2]
results = seasonal_analysis(aoi, year=2024)
```

---

## 📐 Understanding Fire Risk Scores

### Fire Risk Score (0-100)
The comprehensive fire risk score combines multiple factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Vegetation Health** | 40% | Low NDVI = high risk (sparse/stressed vegetation) |
| **Moisture Content** | 30% | Low NDMI = high risk (dry vegetation) |
| **Soil Exposure** | 20% | High bare soil index = high risk |
| **Plant Stress** | 10% | High redness ratio = high risk |

### Risk Classification

| Score Range | Risk Level | Description | Color |
|------------|------------|-------------|-------|
| 0-20 | Very Low | Healthy, dense vegetation with high moisture | 🟢 Dark Green |
| 20-40 | Low | Good vegetation cover, moderate moisture | 🟢 Green |
| 40-60 | Moderate | Mixed conditions, some areas of concern | 🟡 Yellow |
| 60-80 | High | Stressed vegetation, low moisture, fire-prone | 🟠 Orange |
| 80-100 | Very High | Critical conditions, immediate risk | 🔴 Red |

---

## 🔬 Technical Details

### Satellite Data Sources

**Sentinel-2 (Recommended)**
- **Provider:** European Space Agency (ESA)
- **Resolution:** 10m (visible/NIR), 20m (SWIR)
- **Revisit Time:** 5 days
- **Collection:** COPERNICUS/S2_SR_HARMONIZED
- **Bands Used:** B2 (Blue), B3 (Green), B4 (Red), B8 (NIR), B11 (SWIR1), B12 (SWIR2)

**Landsat 8/9**
- **Provider:** NASA/USGS
- **Resolution:** 30m
- **Revisit Time:** 16 days
- **Collection:** LANDSAT/LC08/C02/T1_L2 or LANDSAT/LC09/C02/T1_L2
- **Bands Used:** SR_B2 (Blue), SR_B3 (Green), SR_B4 (Red), SR_B5 (NIR), SR_B6 (SWIR1), SR_B7 (SWIR2)

### Vegetation Indices Formulas

```python
# NDVI - Normalized Difference Vegetation Index
NDVI = (NIR - Red) / (NIR + Red)

# SAVI - Soil Adjusted Vegetation Index (L=0.5)
SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)

# EVI - Enhanced Vegetation Index
EVI = 2.5 * ((NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1))

# NDMI - Normalized Difference Moisture Index
NDMI = (NIR - SWIR) / (NIR + SWIR)

# NBR - Normalized Burn Ratio
NBR = (NIR - SWIR2) / (NIR + SWIR2)

# BSI - Bare Soil Index
BSI = ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))
```

---

## 🗂️ Project Structure

```
fire-risk-analysis/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── fire_vegetation_analysis.py        # Main analysis code
├── examples/
│   ├── california_example.py          # California wildfire analysis
│   ├── custom_location_example.py     # Point-based analysis
│   └── time_series_example.py         # Seasonal comparison
├── outputs/
│   ├── fire_risk_map.html            # Interactive map
│   ├── fire_risk_analysis_gee.png    # Static visualization
│   └── statistics_report.txt         # Analysis report
└── docs/
    ├── SETUP.md                      # Detailed setup guide
    ├── API_REFERENCE.md              # API documentation
    └── TROUBLESHOOTING.md            # Common issues and solutions
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/fire-risk-analysis.git
cd fire-risk-analysis

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies including dev tools
pip install -r requirements.txt
pip install pytest black flake8

# Run tests
pytest tests/

# Format code
black fire_vegetation_analysis.py
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📚 References

- [Google Earth Engine Documentation](https://developers.google.com/earth-engine)
- [Sentinel-2 User Guide](https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi)
- [Landsat 8-9 Data Users Handbook](https://www.usgs.gov/landsat-missions/landsat-8-data-users-handbook)
- [NDVI and Vegetation Indices](https://gisgeography.com/ndvi-normalized-difference-vegetation-index/)
- [Fire Risk Assessment Methods](https://www.mdpi.com/2072-4292/12/19/3254)

---

## 🙏 Acknowledgments

- Google Earth Engine for providing free satellite data access
- European Space Agency (ESA) for Sentinel-2 data
- NASA/USGS for Landsat data
- The open-source Python community

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/fire-risk-analysis/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/fire-risk-analysis/discussions)
- **Email:** your.email@example.com

---

## 🗺️ Roadmap

### Version 1.1 (Coming Soon)
- [ ] Real-time fire detection using thermal bands
- [ ] Historical fire scar mapping
- [ ] Integration with weather data (temperature, humidity, wind)
- [ ] Machine learning fire risk prediction model

### Version 2.0 (Future)
- [ ] Web interface for non-technical users
- [ ] Automated email alerts for high-risk areas
- [ ] Mobile app for field data collection
- [ ] Integration with local fire department systems

---

## ⭐ Star History

If you find this project useful, please consider giving it a star on GitHub!

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/fire-risk-analysis&type=Date)](https://star-history.com/#yourusername/fire-risk-analysis&Date)

---

**Made with ❤️ for wildfire prevention and environmental conservation**
