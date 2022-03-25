import numpy as np
import exiftool
import os
import matplotlib.pyplot as plt


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

    """

    def __init__(self, filename):
        self.filename = filename
        self.metadata = self.get_metadata()
        self.planck   = self.get_planck_coeffs()
        self.width    = self.metadata["APP1:RawThermalImageWidth"]
        self.height   = self.metadata["APP1:RawThermalImageHeight"]
        self.shape    = (self.height, self.width)
        self.raw      = self.extract_raw_image()
        self.temp     = raw_to_temperature(self.raw, self.planck)

    def get_metadata(self):
        """Extract metadata from image file using exiftool"""
        with exiftool.ExifTool() as et:
            self.metadata = et.get_metadata(self.filename)
        return self.metadata

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
        subsequently read using matplotlib's imread.
        """
        metadata = self.metadata
        #fmt = metadata["APP1:RawThermalImageType"]
        os.system(f"exiftool {self.filename} -rawthermalimage -b > temp")
        self.raw = plt.imread("temp")
        os.system("rm temp")
        return self.raw

    # def raw_to_temperature(self):
    #     r"""
    #     Convert RAW thermal image values to temperature, :math:`T`, (in 
    #     Kelvin) via 
    #     .. math::
    #         T = B / \log(R_1/(R_2(S + O)) + F) ,

    #     where :math:`B = [1300--1600]`, :math:`F = [0.5--2]`, :math:`O < 0`, 
    #     :math:`R_1` and :math:`R_2` are Planck constants that can be found 
    #     from the exif data, and :math:`S` is the (16-bit) RAW value.

    #     See https://exiftool.org/forum/index.php?topic=4898.60
    #     """
    #     planck = self.planck
    #     S = self.raw
    #     B = planck["B"]
    #     F = planck["F"]
    #     O = planck["O"]
    #     R1 = planck["R1"]
    #     R2 = planck["R2"]
    #     self.temp = B / np.log(R1 / (R2*(S + O)) + F)
    #     return 


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
    return B / np.log(R1 / (R2*(S + O)) + F)
    



if __name__ == "__main__":
    import sys

    filename = sys.argv[1]
    im = FLIR_image(filename)
    print(im.extract_raw_image().shape)
