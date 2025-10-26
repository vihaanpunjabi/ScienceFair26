import ssl
import certifi
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

import ee

PROJECT_ID = 'sciencef-476305'

print(f"🔐 Authenticating with YOUR project: {PROJECT_ID}")
print("This will open a browser - make sure to sign in!")

# Authenticate (simpler syntax)
ee.Authenticate()

print("✅ Authentication complete!")
print(f"🚀 Initializing with project: {PROJECT_ID}")

# Initialize with your project explicitly
ee.Initialize(project=PROJECT_ID)

print("✅ Success! Testing...")
point = ee.Geometry.Point([-122.262, 37.8719])
info = point.getInfo()
print(f"✅ Earth Engine working with project {PROJECT_ID}!")
print(f"   Test result: {info['type']}")
