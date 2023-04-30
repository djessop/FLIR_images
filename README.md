# FLIR_images

Provides a python class (FLIR_images) for extracting raw thermal image data
from FLIR radiometric jpegs.

Current usage relies on system calls to "exiftool".  Future versions will
(hopefully) incorporate all functions internally.

Example usage
-------------
In python (i.e. IDLE, ipython)
```
from tirAnalysis.FLIR_images import FLIR_image
im = FLIR_image("DJI_1098_R.JPG", bitdepth=64)
# Show "Planck" constants for converting RAW thermal image to temperature
print(im.planck)
# Print basic statistics for the distribution of temperatures in the image
print(im.T_stats)
```

From command line
```
python FLIR_image.py <FILENAME>
```



Requirements
------------
```
tifftile
numpy
PyExifTool
```

All required modules can be installed by doing
```pip install -r requirements.txt```


TO DO:
------
- Atmospheric transmissivity and surface reflectivity
- Provide bash script to do things ex-python