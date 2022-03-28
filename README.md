# FLIR_images

Provides a python class (FLIR_images) for extracting raw thermal image data
from FLIR radiometric jpegs.


Example usage
-------------
In python (i.e. IDLE, ipython)
```
from tirAnalysis.FLIR_images import FLIR_image
im = FLIR_image("DJI_1098_R.JPG")
# Show "Planck" constants for converting RAW thermal image to temperature
print(im.planck)
# Print basic statistics for the distribution of temperatures in the image
print(im.T_stats)
```

From command line
```
python FLIR_image.py DJI_1090_R.JPG
```
Replace ```DJI_1090_R.JPG``` with the file that you wish to process.  




Requirements
------------
```
matplotlib
numpy
PyExifTool
```

All required modules can be installed by doing
```pip install -r requirements.txt```
