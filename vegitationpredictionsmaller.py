"""
Fire-Prone Vegetation Analysis using Google Earth Engine
This code analyzes vegetation and fire risk using satellite data from GEE
"""

# Fix SSL certificate issues on Mac
import ssl
import certifi
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

import ee
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import seaborn as sns
from datetime import datetime, timedelta
import geemap
import folium

# ============ CONFIGURATION ============
# Your Earth Engine Project ID
PROJECT_ID = 'sciencef-476305'

# Initialize Earth Engine
def initialize_earth_engine(project_id=None):
    """Initialize Earth Engine with automatic authentication"""
    if project_id is None:
        project_id = PROJECT_ID
    
    try:
        # Try to initialize with project (force the project parameter)
        ee.Initialize(project=project_id)
        print(f"✅ Earth Engine initialized successfully with project: {project_id}")
        return True
    except Exception as e:
        print(f"⚠️  Not authenticated yet: {e}")
        print(f"\n🔐 Starting authentication process for project: {project_id}...")
        print("A browser window will open for you to sign in with Google.")
        
        try:
            # Authenticate
            ee.Authenticate()
            # Initialize after authentication with project (explicitly set)
            ee.Initialize(project=project_id)
            print(f"✅ Authentication successful! Earth Engine is ready with project: {project_id}")
            return True
        except Exception as auth_error:
            print(f"❌ Authentication failed: {auth_error}")
            print("\n📝 Troubleshooting steps:")
            print("1. Make sure you've enabled the Earth Engine API")
            print("2. Check your project ID is correct: " + project_id)
            print("3. Visit: https://console.cloud.google.com/apis/library/earthengine.googleapis.com")
            print(f"4. Make sure the API is enabled for project: {project_id}")
            return False

# Initialize at module import
if not initialize_earth_engine():
    print("\n⚠️  WARNING: Earth Engine not initialized.")
    print("Please run auth_fix.py first to authenticate.")


class GEEFireRiskAnalyzer:
    """
    Fire Risk Analyzer using Google Earth Engine data
    """
    
    def __init__(self, area_of_interest, start_date, end_date, satellite='sentinel2'):
        """
        Initialize analyzer with Earth Engine data
        
        Parameters:
        -----------
        area_of_interest : ee.Geometry or list
            Area to analyze. Can be:
            - ee.Geometry.Point([lon, lat])
            - ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])
            - [lon_min, lat_min, lon_max, lat_max] (will be converted)
        start_date : str
            Start date in format 'YYYY-MM-DD'
        end_date : str
            End date in format 'YYYY-MM-DD'
        satellite : str
            'sentinel2' or 'landsat8' or 'landsat9'
        """
        # Convert area_of_interest to ee.Geometry if needed
        if isinstance(area_of_interest, list):
            if len(area_of_interest) == 2:  # Point [lon, lat]
                self.aoi = ee.Geometry.Point(area_of_interest)
            elif len(area_of_interest) == 4:  # Rectangle
                self.aoi = ee.Geometry.Rectangle(area_of_interest)
            else:
                raise ValueError("area_of_interest list must be [lon, lat] or [lon_min, lat_min, lon_max, lat_max]")
        else:
            self.aoi = area_of_interest
        
        self.start_date = start_date
        self.end_date = end_date
        self.satellite = satellite.lower()
        
        # Load imagery
        self.image = self._load_imagery()
        self.image_data = None  # Will store downloaded numpy arrays
        
    def _load_imagery(self):
        """
        Load satellite imagery from Earth Engine
        """
        if self.satellite == 'sentinel2':
            # Sentinel-2 Level 2A (atmospherically corrected)
            collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                .filterBounds(self.aoi) \
                .filterDate(self.start_date, self.end_date) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            
            print(f"Found {collection.size().getInfo()} Sentinel-2 images")
            
            # Get median composite (cloud-free)
            image = collection.median()
            
            # Select and rename bands
            image = image.select(
                ['B2', 'B3', 'B4', 'B8', 'B11', 'B12'],
                ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
            )
            
        elif self.satellite in ['landsat8', 'landsat9']:
            # Landsat 8/9 Collection 2 Level 2
            dataset = 'LANDSAT/LC08/C02/T1_L2' if self.satellite == 'landsat8' else 'LANDSAT/LC09/C02/T1_L2'
            
            collection = ee.ImageCollection(dataset) \
                .filterBounds(self.aoi) \
                .filterDate(self.start_date, self.end_date) \
                .filter(ee.Filter.lt('CLOUD_COVER', 20))
            
            print(f"Found {collection.size().getInfo()} {self.satellite.upper()} images")
            
            # Get median composite
            image = collection.median()
            
            # Apply scaling factors and select bands
            def apply_scale_factors(img):
                optical = img.select('SR_B.').multiply(0.0000275).add(-0.2)
                thermal = img.select('ST_B.*').multiply(0.00341802).add(149.0)
                return img.addBands(optical, None, True).addBands(thermal, None, True)
            
            image = apply_scale_factors(image)
            
            # Select and rename bands
            image = image.select(
                ['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7'],
                ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
            )
        else:
            raise ValueError("satellite must be 'sentinel2', 'landsat8', or 'landsat9'")
        
        return image
    
    def calculate_ndvi(self):
        """Calculate NDVI"""
        ndvi = self.image.normalizedDifference(['nir', 'red']).rename('NDVI')
        return ndvi
    
    def calculate_savi(self, L=0.5):
        """Calculate SAVI (Soil Adjusted Vegetation Index)"""
        nir = self.image.select('nir')
        red = self.image.select('red')
        
        savi = nir.subtract(red).divide(
            nir.add(red).add(L)
        ).multiply(1 + L).rename('SAVI')
        
        return savi
    
    def calculate_evi(self):
        """Calculate EVI (Enhanced Vegetation Index)"""
        nir = self.image.select('nir')
        red = self.image.select('red')
        blue = self.image.select('blue')
        
        evi = nir.subtract(red).divide(
            nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)
        ).multiply(2.5).rename('EVI')
        
        return evi
    
    def calculate_ndmi(self):
        """Calculate NDMI (Normalized Difference Moisture Index)"""
        ndmi = self.image.normalizedDifference(['nir', 'swir1']).rename('NDMI')
        return ndmi
    
    def calculate_nbr(self):
        """Calculate NBR (Normalized Burn Ratio)"""
        nbr = self.image.normalizedDifference(['nir', 'swir2']).rename('NBR')
        return nbr
    
    def calculate_bsi(self):
        """Calculate BSI (Bare Soil Index)"""
        swir1 = self.image.select('swir1')
        red = self.image.select('red')
        nir = self.image.select('nir')
        blue = self.image.select('blue')
        
        bsi = swir1.add(red).subtract(nir).subtract(blue).divide(
            swir1.add(red).add(nir).add(blue)
        ).rename('BSI')
        
        return bsi
    
    def analyze_plant_color(self):
        """Analyze plant color characteristics"""
        greenness = self.image.select('nir').subtract(self.image.select('red')).rename('Greenness')
        redness = self.image.select('red').divide(self.image.select('nir').add(0.0001)).rename('Redness')
        brightness = self.image.select(['red', 'green', 'blue']).reduce(ee.Reducer.mean()).rename('Brightness')
        
        return {
            'greenness': greenness,
            'redness': redness,
            'brightness': brightness
        }
    
    def calculate_fire_risk_score(self):
        """
        Calculate comprehensive fire risk score
        
        Returns:
        --------
        ee.Image : Fire risk score (0-100)
        """
        # Calculate indices
        ndvi = self.calculate_ndvi()
        ndmi = self.calculate_ndmi()
        bsi = self.calculate_bsi()
        
        # Factor 1: Vegetation health (40% weight)
        # Normalize NDVI from [-1,1] to [0,1], then invert (low veg = high risk)
        veg_risk = ndvi.add(1).divide(2).multiply(-1).add(1).multiply(40)
        
        # Factor 2: Moisture content (30% weight)
        # Normalize NDMI from [-1,1] to [0,1], then invert (low moisture = high risk)
        moisture_risk = ndmi.add(1).divide(2).multiply(-1).add(1).multiply(30)
        
        # Factor 3: Soil/bare ground (20% weight)
        # Normalize BSI from [-1,1] to [0,1] (high bare soil = high risk)
        soil_risk = bsi.add(1).divide(2).multiply(20)
        
        # Factor 4: Plant stress (10% weight)
        redness = self.analyze_plant_color()['redness']
        stress_risk = redness.multiply(10).clamp(0, 10)
        
        # Combine all factors
        fire_risk = veg_risk.add(moisture_risk).add(soil_risk).add(stress_risk).clamp(0, 100)
        fire_risk = fire_risk.rename('Fire_Risk_Score')
        
        return fire_risk
    
    def classify_fire_risk(self, fire_risk_score):
        """
        Classify fire risk into categories
        
        Returns:
        --------
        ee.Image : Risk classes (1-5)
        """
        risk_classes = ee.Image(1) \
            .where(fire_risk_score.gte(20), 2) \
            .where(fire_risk_score.gte(40), 3) \
            .where(fire_risk_score.gte(60), 4) \
            .where(fire_risk_score.gte(80), 5) \
            .rename('Risk_Class')
        
        return risk_classes
    
    def create_analysis_composite(self):
        """
        Create composite image with all analysis layers
        """
        ndvi = self.calculate_ndvi()
        savi = self.calculate_savi()
        evi = self.calculate_evi()
        ndmi = self.calculate_ndmi()
        nbr = self.calculate_nbr()
        bsi = self.calculate_bsi()
        fire_risk = self.calculate_fire_risk_score()
        risk_class = self.classify_fire_risk(fire_risk)
        
        color_metrics = self.analyze_plant_color()
        
        # Combine all into single image
        composite = self.image.addBands([
            ndvi, savi, evi, ndmi, nbr, bsi,
            color_metrics['greenness'],
            color_metrics['redness'],
            color_metrics['brightness'],
            fire_risk,
            risk_class
        ])
        
        return composite
    
    def visualize_interactive_map(self):
        """
        Create interactive map with all layers using geemap
        """
        # Create map centered on AOI
        center = self.aoi.centroid().coordinates().getInfo()
        Map = geemap.Map(center=[center[1], center[0]], zoom=12)
        
        # Add base layers
        Map.addLayer(self.image, 
                    {'bands': ['red', 'green', 'blue'], 'min': 0, 'max': 0.3},
                    'True Color')
        
        # Add NDVI
        ndvi_viz = {'min': -0.2, 'max': 0.8, 'palette': ['red', 'yellow', 'green']}
        Map.addLayer(self.calculate_ndvi(), ndvi_viz, 'NDVI', False)
        
        # Add NDMI (Moisture)
        ndmi_viz = {'min': -0.5, 'max': 0.5, 'palette': ['red', 'yellow', 'blue']}
        Map.addLayer(self.calculate_ndmi(), ndmi_viz, 'NDMI (Moisture)', False)
        
        # Add Fire Risk Score
        fire_risk_viz = {'min': 0, 'max': 100, 'palette': ['green', 'yellow', 'orange', 'red', 'darkred']}
        Map.addLayer(self.calculate_fire_risk_score(), fire_risk_viz, 'Fire Risk Score')
        
        # Add Fire Risk Classification
        risk_class_viz = {'min': 1, 'max': 5, 'palette': ['darkgreen', 'green', 'yellow', 'orange', 'red']}
        Map.addLayer(self.classify_fire_risk(self.calculate_fire_risk_score()), 
                    risk_class_viz, 'Fire Risk Classification')
        
        # Add AOI boundary
        Map.addLayer(self.aoi, {'color': 'white'}, 'Area of Interest')
        
        # Add layer control
        Map.add_layer_control()
        
        return Map
    
    def download_data_for_local_analysis(self, scale=30):
        """
        Download data as numpy arrays for local processing
        
        Parameters:
        -----------
        scale : int
            Pixel resolution in meters (10 for Sentinel-2, 30 for Landsat)
        
        Returns:
        --------
        dict : Dictionary with numpy arrays for each band
        """
        print(f"Downloading data at {scale}m resolution...")
        print("This may take a few minutes depending on area size...")
        
        # Create composite
        composite = self.create_analysis_composite()
        
        # Get region
        region = self.aoi.bounds().getInfo()['coordinates']
        
        # Download bands
        try:
            # Sample the image to get data
            sample = composite.sampleRectangle(region=self.aoi, defaultValue=0)
            
            # Convert to numpy arrays
            data = {}
            band_names = composite.bandNames().getInfo()
            
            for band in band_names:
                try:
                    data[band] = np.array(sample.get(band).getInfo())
                except:
                    print(f"Warning: Could not download band {band}")
            
            self.image_data = data
            print(f"Successfully downloaded {len(data)} bands")
            return data
            
        except Exception as e:
            print(f"Error downloading data: {e}")
            print("Try reducing the area size or using export_to_drive() for large areas")
            return None
    
    def export_to_drive(self, description='fire_risk_analysis', scale=30):
        """
        Export analysis to Google Drive (better for large areas)
        
        Parameters:
        -----------
        description : str
            Name for the exported file
        scale : int
            Pixel resolution in meters
        """
        composite = self.create_analysis_composite()
        
        task = ee.batch.Export.image.toDrive(
            image=composite,
            description=description,
            scale=scale,
            region=self.aoi,
            maxPixels=1e13,
            fileFormat='GeoTIFF'
        )
        
        task.start()
        print(f"Export task started: {description}")
        print(f"Check status at: https://code.earthengine.google.com/tasks")
        print(f"Files will appear in your Google Drive under 'Earthengine' folder")
        
        return task
    
    def generate_statistics_report(self):
        """
        Generate summary statistics for the area
        """
        print("=" * 70)
        print("FIRE RISK VEGETATION ANALYSIS REPORT (Google Earth Engine)")
        print("=" * 70)
        
        # Calculate statistics for the AOI
        ndvi = self.calculate_ndvi()
        savi = self.calculate_savi()
        ndmi = self.calculate_ndmi()
        fire_risk = self.calculate_fire_risk_score()
        risk_class = self.classify_fire_risk(fire_risk)
        
        # Reducer for statistics
        stats_reducer = ee.Reducer.mean() \
            .combine(ee.Reducer.stdDev(), '', True) \
            .combine(ee.Reducer.min(), '', True) \
            .combine(ee.Reducer.max(), '', True)
        
        print("\n1. VEGETATION INDICES SUMMARY")
        print("-" * 70)
        
        # NDVI stats
        ndvi_stats = ndvi.reduceRegion(
            reducer=stats_reducer,
            geometry=self.aoi,
            scale=30,
            maxPixels=1e9
        ).getInfo()
        
        print(f"NDVI - Mean: {ndvi_stats.get('NDVI_mean', 0):.3f}, "
              f"Std: {ndvi_stats.get('NDVI_stdDev', 0):.3f}")
        print(f"       Range: [{ndvi_stats.get('NDVI_min', 0):.3f}, "
              f"{ndvi_stats.get('NDVI_max', 0):.3f}]")
        
        # SAVI stats
        savi_stats = savi.reduceRegion(
            reducer=stats_reducer,
            geometry=self.aoi,
            scale=30,
            maxPixels=1e9
        ).getInfo()
        
        print(f"SAVI - Mean: {savi_stats.get('SAVI_mean', 0):.3f}, "
              f"Std: {savi_stats.get('SAVI_stdDev', 0):.3f}")
        
        # NDMI stats
        ndmi_stats = ndmi.reduceRegion(
            reducer=stats_reducer,
            geometry=self.aoi,
            scale=30,
            maxPixels=1e9
        ).getInfo()
        
        print(f"NDMI - Mean: {ndmi_stats.get('NDMI_mean', 0):.3f}, "
              f"Std: {ndmi_stats.get('NDMI_stdDev', 0):.3f}")
        
        print("\n2. FIRE RISK DISTRIBUTION")
        print("-" * 70)
        
        # Calculate area for each risk class
        area_image = ee.Image.pixelArea()
        
        for risk_level, label in enumerate(['Very Low', 'Low', 'Moderate', 'High', 'Very High'], 1):
            mask = risk_class.eq(risk_level)
            area = area_image.updateMask(mask).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=self.aoi,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            area_km2 = area.get('area', 0) / 1e6
            print(f"{label:12s}: {area_km2:.2f} km²")
        
        print("\n3. OVERALL FIRE RISK ASSESSMENT")
        print("-" * 70)
        
        risk_stats = fire_risk.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=self.aoi,
            scale=30,
            maxPixels=1e9
        ).getInfo()
        
        avg_risk = risk_stats.get('Fire_Risk_Score', 0)
        print(f"Average Fire Risk Score: {avg_risk:.2f}/100")
        
        if avg_risk < 30:
            risk_level = "LOW"
            recommendation = "Area shows healthy vegetation with low fire risk."
        elif avg_risk < 50:
            risk_level = "MODERATE"
            recommendation = "Monitor conditions. Some areas may be fire-prone."
        elif avg_risk < 70:
            risk_level = "HIGH"
            recommendation = "High fire risk. Implement prevention measures."
        else:
            risk_level = "VERY HIGH"
            recommendation = "Critical fire risk. Immediate action recommended."
        
        print(f"Overall Risk Level: {risk_level}")
        print(f"Recommendation: {recommendation}")
        
        print("\n" + "=" * 70)
    
    def visualize_local_analysis(self, data=None):
        """
        Visualize downloaded data using matplotlib
        """
        if data is None:
            if self.image_data is None:
                print("No data available. Run download_data_for_local_analysis() first.")
                return
            data = self.image_data
        
        fig, axes = plt.subplots(3, 3, figsize=(18, 16))
        fig.suptitle('Fire Risk Vegetation Analysis (Google Earth Engine)', 
                     fontsize=16, fontweight='bold')
        
        # Plot each metric
        metrics = [
            ('NDVI', 'RdYlGn', -0.2, 0.8),
            ('SAVI', 'RdYlGn', -0.2, 0.8),
            ('EVI', 'RdYlGn', -0.2, 0.8),
            ('NDMI', 'RdYlBu', -0.5, 0.5),
            ('Redness', 'YlOrRd', 0, 2),
            ('BSI', 'YlOrBr', -1, 1),
            ('Greenness', 'Greens', 0, 0.5),
            ('Fire_Risk_Score', 'YlOrRd', 0, 100),
            ('Risk_Class', ListedColormap(['darkgreen', 'green', 'yellow', 'orange', 'red']), 1, 5)
        ]
        
        for idx, (name, cmap, vmin, vmax) in enumerate(metrics):
            row, col = idx // 3, idx % 3
            
            if name in data:
                im = axes[row, col].imshow(data[name], cmap=cmap, vmin=vmin, vmax=vmax)
                axes[row, col].set_title(name.replace('_', ' '))
                plt.colorbar(im, ax=axes[row, col])
            else:
                axes[row, col].text(0.5, 0.5, f'{name}\nNot Available', 
                                   ha='center', va='center', 
                                   transform=axes[row, col].transAxes)
            
            axes[row, col].set_xticks([])
            axes[row, col].set_yticks([])
        
        plt.tight_layout()
        plt.savefig('fire_risk_analysis_gee.png', dpi=300, bbox_inches='tight')
        print("Visualization saved to 'fire_risk_analysis_gee.png'")
        plt.show()


# ============ EXAMPLE USAGE ============

def example_california_wildfire_area():
    """
    Example: Analyze fire-prone area in California
    """
    print("Example: California Fire Risk Analysis")
    print("=" * 70)
    
    # Define area of interest (Santa Monica Mountains, CA - fire-prone area)
    # Format: [lon_min, lat_min, lon_max, lat_max]
    california_aoi = [-118.7, 34.0, -118.5, 34.2]
    
    # Or use a point and buffer
    # point = ee.Geometry.Point([-118.6, 34.1])
    # aoi = point.buffer(5000)  # 5km buffer
    
    # Date range (use recent dates, within last 2 years for best results)
    start_date = '2024-06-01'
    end_date = '2024-09-30'
    
    # Initialize analyzer
    analyzer = GEEFireRiskAnalyzer(
        area_of_interest=california_aoi,
        start_date=start_date,
        end_date=end_date,
        satellite='sentinel2'  # or 'landsat8' or 'landsat9'
    )
    
    # Generate statistics report
    print("\nGenerating statistics report...")
    analyzer.generate_statistics_report()
    
    # Create interactive map
    print("\nCreating interactive map...")
    map_obj = analyzer.visualize_interactive_map()
    map_obj.save('fire_risk_map.html')
    print("Interactive map saved to 'fire_risk_map.html'")
    
    # Download data for local analysis (for small areas)
    # Note: The California area might be too large for direct download
    # Uncomment the following lines for smaller areas (< 5km x 5km)
    
    # print("\nDownloading data for local visualization...")
    # data = analyzer.download_data_for_local_analysis(scale=30)
    # if data:
    #     analyzer.visualize_local_analysis(data)
    
    # For large areas, export to Google Drive instead
    print("\nFor large area analysis, use Google Drive export:")
    print("Uncomment the line below to export to your Google Drive")
    # analyzer.export_to_drive('california_fire_risk', scale=30)
    
    return analyzer


def example_custom_location(lon, lat, buffer_km=5):
    """
    Analyze any location by coordinates
    
    Parameters:
    -----------
    lon : float
        Longitude
    lat : float
        Latitude
    buffer_km : float
        Buffer distance in kilometers
    """
    # Create point and buffer
    point = ee.Geometry.Point([lon, lat])
    aoi = point.buffer(buffer_km * 1000)  # Convert km to meters
    
    # Use recent dates
    today = datetime.now()
    end_date = today.strftime('%Y-%m-%d')
    start_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')  # Last 3 months
    
    analyzer = GEEFireRiskAnalyzer(
        area_of_interest=aoi,
        start_date=start_date,
        end_date=end_date,
        satellite='sentinel2'
    )
    
    analyzer.generate_statistics_report()
    
    map_obj = analyzer.visualize_interactive_map()
    map_obj.save(f'fire_risk_map_{lat}_{lon}.html')
    
    return analyzer


def example_small_area_analysis():
    """
    Smaller area for complete analysis with static visualizations
    """
    print("\n" + "=" * 70)
    print("Small Area Fire Risk Analysis (with static plots)")
    print("=" * 70)
    
    # Very small area - about 2km x 2km in Santa Monica Mountains
    # This is small enough to download all bands for matplotlib visualization
    small_aoi = [-118.62, 34.08, -118.60, 34.10]
    
    print(f"\nAnalyzing smaller area: {small_aoi}")
    print("Area size: ~2km x 2km")
    
    # Date range
    start_date = '2024-06-01'
    end_date = '2024-09-30'
    
    # Initialize analyzer
    analyzer = GEEFireRiskAnalyzer(
        area_of_interest=small_aoi,
        start_date=start_date,
        end_date=end_date,
        satellite='sentinel2'
    )
    
    # Generate statistics report
    print("\n📊 Generating statistics report...")
    analyzer.generate_statistics_report()
    
    # Create interactive map
    print("\n🗺️  Creating interactive map...")
    map_obj = analyzer.visualize_interactive_map()
    map_obj.save('fire_risk_map_small.html')
    print("✅ Interactive map saved to 'fire_risk_map_small.html'")
    
    # Download data for local analysis (should work for small area)
    print("\n⬇️  Downloading data for static visualization...")
    print("This may take 1-2 minutes...")
    data = analyzer.download_data_for_local_analysis(scale=10)  # 10m resolution for Sentinel-2
    
    if data and len(data) > 0:
        print(f"✅ Successfully downloaded {len(data)} bands!")
        print("\n📈 Creating static visualizations...")
        analyzer.visualize_local_analysis(data)
        print("✅ Static visualization saved to 'fire_risk_analysis_gee.png'")
    else:
        print("⚠️  Could not download data. Area might still be too large.")
        print("   Try an even smaller area or check your internet connection.")
    
    return analyzer


# Main execution
if __name__ == "__main__":
    print("Fire-Prone Vegetation Analysis with Google Earth Engine")
    print("=" * 70)
    print("\nNOTE: Make sure you've authenticated first by running auth_fix.py")
    print("=" * 70)
    
    # Option 1: Run large area example (statistics + interactive map only)
    print("\n🔥 Running LARGE area analysis (California)...")
    analyzer_large = example_california_wildfire_area()
    
    # Option 2: Run small area example (statistics + interactive map + static plots)
    print("\n🔥 Running SMALL area analysis (with static plots)...")
    analyzer_small = example_small_area_analysis()
    
    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print("\nGenerated files:")
    print("  📁 fire_risk_map.html - Large area interactive map")
    print("  📁 fire_risk_map_small.html - Small area interactive map")
    print("  📁 fire_risk_analysis_gee.png - Small area static visualization")
    print("\n💡 Tip: Open the HTML files in your browser to explore the maps!")
    print("=" * 70)
