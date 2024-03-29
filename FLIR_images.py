#!/usr/bin/env python3
# coding: utf8

"""
FLIR_image.py

Provides:
FLIR_image : class 
    Provides methods for handling FLIR thermal images
raw_to_temperature : function
     Converts RAW thermal image values to temperature
temperature_to_raw : function
     Converts temperature values to RAW thermal image

See
https://exiftool.org/forum/index.php?topic=4898.60
"""

import os
import numpy as np
import exiftool
import tifffile


# Example of Planck constants
planck = {'R1': 385517, 'B': 1428, 'F': 1, 'O': -72, 'R2': 1}

class FLIR_image():
    """
    Class for handling FLIR thermal images.

    Provides the following methods:
        get_metadata : 
        get_planck_coeffs :
        extract_raw_image : extracts the raw thermal image from metadata and 
            saves it as an appropriately named file in the current directory.
        raw_to_temperature : converts raw thermal image to temperature using
            the Planck coefficients defined in the metadata.

    TO DO:
    ------
    - Include atmospheric transmissivity calculations

    """

    def __init__(self, filename, e=1., tau=1., bitdepth=16, outtype='raw',
                 includeexif=True, removeoriginal=True, thermalim=True):
        self.filename  = filename
        self.metadata  = self.get_metadata()
        self.position  = self.get_position()
        self.outtype   = None
        self.thermalim = thermalim
        if self.thermalim:
            self.raw_fmt  = self.metadata["APP1:RawThermalImageType"].lower()
            self.planck   = self.get_planck_coeffs()
            self.raw      = self.extract_raw_image()
            self.temp     = raw_to_temperature(self.raw, self.planck)
            self.T_stats  = {"T_min": self.temp.min(),
                             "T_max": self.temp.max(),
                             "T_mean": self.temp.mean(),
                             "T_std": self.temp.std(),
                             "T_med": np.median(self.temp)}
            self.e        = e    # surface emissivity
            self.tau      = tau  # atmospheric transmissivity
            self.outtype  = outtype
            self.bitdepth = bitdepth  # choose 16, 32 or 64 bits

        self.width  = self.metadata["File:ImageWidth"]
        self.height = self.metadata["File:ImageHeight"]
        self.shape  = (self.height, self.width)
        self.includeexif    = includeexif
        self.removeoriginal = removeoriginal


    def get_metadata(self):
        """Extract metadata from image file using exiftool"""
        with exiftool.ExifTool() as et:
            self.metadata = et.get_metadata(self.filename)
        return self.metadata


    def get_position(self):
        """ Extract "GPS" position from metadata """
        self.position = {}
        self.metadata['EXIF:GPSLatitude']  = None
        self.metadata['EXIF:GPSLongitude'] = None
        self.metadata['EXIF:GPSAltitude']  = None
        if 'EXIF:GPSLatitude' in self.metadata.keys():
            self.position['latitude']  = self.metadata['EXIF:GPSLatitude']
        if 'EXIF:GPSLongitude' in self.metadata.keys():
            self.position['longitude'] = self.metadata['EXIF:GPSLongitude']
        if 'EXIF:GPSAltitude' in self.metadata.keys():
            self.position['altitude']  = self.metadata['EXIF:GPSAltitude']
            
        return self.position


    def get_planck_coeffs(self):
        self.planck = {}
        for key, val in self.metadata.items():
            if "planck" in key.lower():
                self.planck[key[11:]] = val
        return self.planck
    

    def extract_raw_image(self):
        """
        Extract raw thermal image from metadata.  Requires exiftool to be 
        installed on the system, and creates a temporary image file that is 
        subsequently read using tifffile's imread.
        """
        metadata = self.metadata
        fmt = metadata["APP1:RawThermalImageType"].lower()
        os.system(f"exiftool {self.filename} -rawthermalimage -b > "
                  + f"{self.filename}_temp")
        # with exiftool.ExifTool() as et:
        #     et.execute(bytes(self.filename, "utf-8"),
        #                b"-rawthermalimage -b > temp")

        # Only do this if the format is tiff.  Method should reflect image
        # type
        if 'tif' in fmt:
            self.raw = tifffile.imread(f"{self.filename}_temp")
        if fmt == 'png':
            from matplotlib.pyplot import imread
            self.raw = imread(f"{self.filename}_temp")
        os.system(f"rm {self.filename}_temp")
        return self.raw


    def save_data(self, filename=None):
        """
        Write image data to file using tifffile.imwrite.

        Parameters
        ----------
        type : str (optional)
            Selects between RAW ("raw") or temperature data as the image 
            contents.  Default is "raw".
        filename : str (optional)
            Specify an alternative output filename.  By default, this will be 
            the same as the input file except that the extension (e.g. jpg or 
            JPG) will be replaced by "tiff".  

        Returns
        -------
        None

        """
        if not self.thermalim:
            raise AttributeError('"save_data" method available only for '
                                 'thermal images')

        out_fname = ".".join(self.filename.split(".")[:-1])
        if self.outtype.lower() == "raw":
            data = self.raw.astype('uint16')
        else:
            out_fname += "_T"
            data = self.temp
        out_fname += "." + self.raw_fmt

        if filename is not None:
            out_fname = filename

        datatype = 'float16'
        if self.bitdepth == 16:
            datatype = 'uint16'

        tifffile.imwrite(out_fname, data.astype(datatype))
        print(f"Saving {out_fname}...")

        # overwrite (limited) exif data will full metadata from original image
        if self.includeexif:
            with exiftool.ExifTool() as et:
                et.execute(b"-tagsfromfile",
                           bytes(self.filename, "utf-8"),
                           bytes(out_fname, "utf-8"))

        if self.removeoriginal:
            os.remove(out_fname + '_original')
        
        return


def raw_to_temperature(S, planck):
    r"""
    Convert RAW thermal image values to temperature, :math:`T`, (in 
    Kelvin) via 
    .. math::
        T = B / \log(R_1/(R_2(S + O)) + F) ,

    where :math:`B = [1300--1600]`, :math:`F = [0.5--2]`, :math:`O < 0`, 
    :math:`R_1` and :math:`R_2` are Planck constants that can be found 
    from the exif data, and :math:`S` is the (16-bit) RAW value.

    See https://exiftool.org/forum/index.php?topic=4898.60
    """
    B = planck["B"]
    F = planck["F"]
    O = planck["O"]
    R1 = planck["R1"]
    R2 = planck["R2"]

    data = B / np.log(R1 / (R2*(S + O)) + F)
    
    return data


def temperature_to_raw(T, planck):
    r"""
    Convert absolute temperatures, :math:`T`, to RAW thermal image values via
    .. math::
        S = R_1 / (R_2(exp(B/T) - F)) - O ,

    where :math:`B = [1300--1600]`, :math:`F = [0.5--2]`, :math:`O < 0`, 
    :math:`R_1` and :math:`R_2` are Planck constants that can be found 
    from the exif data, and :math:`S` is the (16-bit) RAW value.

    See https://exiftool.org/forum/index.php?topic=4898.60
    """
    B = planck["B"]
    F = planck["F"]
    O = planck["O"]
    R1 = planck["R1"]
    R2 = planck["R2"]
    return (R1 / (R2*(np.exp(B/T) - F)) - O).astype('uint16')


if __name__ == "__main__":
    import sys
    import os

    filename = sys.argv[1]
    out_type = "raw"
    if len(sys.argv) > 2:
        out_type = sys.argv[2]
    #print(out_type)
    im = FLIR_image(filename, bitdepth=16, outtype=out_type)
    im.save_data()

    
    #print(im.extract_raw_image().shape)
    
