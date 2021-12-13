import cv2
import numpy as np
from dataclasses import replace
from napari_live_recording.common import ROI
from napari_live_recording.control.devices.interface import (
    ICamera,
    NumberParameter,
    ListParameter
)
from typing import Union, Any
from sys import platform
# version:1.0.1905.9051
from PIL import Image

import napari_live_recording.control.gxipy as gx

class GxiPy(ICamera):

    msExposure = {
        "1 s":  0,
        "500 ms": -1,
        "250 ms": -2,
        "125 ms": -3,
        "62.5 ms": -4,
        "31.3 ms": -5,
        "15.6 ms": -6, # default
        "7.8 ms": -7,
        "3.9 ms": -8,
        "2 ms": -9,
        "976.6 us": -10,
        "488.3 us": -11,
        "244.1 us": -12,
        "122.1 us": -13
    }
    Gain = {
        "0": 0,
        "5": 5, 
        "10": 10,
        "15": 15,
        "20": 20
    }

    pixelFormats = {
        "RGB" : cv2.COLOR_BGR2RGB, # default
        "RGBA" : cv2.COLOR_BGR2RGBA,
        "BGR" : None,
        "Grayscale" : cv2.COLOR_RGB2GRAY
    }

    def __init__(self, name: str, deviceID: Union[str, int]) -> None:
        """GxiPy VideoCapture wrapper

        Args:
            name (str): user-defined self.camera name.
            deviceID (Union[str, int]): self.camera identifier.
        """


        # create a device manager
        self.device_manager = gx.DeviceManager()
        self.dev_num, dev_info_list = self.device_manager.update_device_list()
        if self.dev_num == 0:
            print("Number of enumerated devices is 0")
            return

        # open the first device
        self.cam = self.device_manager.open_device_by_index(1)

        binning = 4
        self.cam.BinningHorizontal.set(binning)
        self.cam.BinningVertical.set(binning)

        # set continuous acquisition
        self.cam.TriggerMode.set(gx.GxSwitchEntry.OFF)

        # set exposure
        self.cam.ExposureTime.set(10000)

        # set gain
        self.cam.Gain.set(10.0)

        # start data acquisition
        self.cam.stream_on()

        # read GxiPy parameters
        width = self.cam.Width.get() 
        height = self.cam.Height.get() 
        
        # initialize region of interest
        # steps for height, width and offsets
        # are by default 1. We leave them as such
        sensorShape = ROI(offset_x=0, offset_y=0, height=height, width=width)
        
        parameters = {}

        # exposure time in GxiPy is treated differently on Windows, 
        # as exposure times may only have a finite set of values
        if platform.startswith("win"):
            parameters["Exposure time"] = ListParameter(value=self.msExposure["15.6 ms"], 
                                                        options=list(self.msExposure.keys()), 
                                                        editable=True)
            parameters["Gain"] = ListParameter(value=self.Gain["0"], 
                                               options=list(self.Gain.keys(), 
                                                            editable=True))
        else:
            parameters["Exposure time"] = NumberParameter(value=1,
                                                        valueLimits=(1, 10000),
                                                        unit="ms",
                                                        editable=True)
            parameters["Gain"] = NumberParameter(value=0,
                                                        valueLimits=(0, 20),
                                                        unit="a.U.",
                                                        editable=True)
            
        parameters["Pixel format"] = ListParameter(value=self.pixelFormats["RGB"],
                                                options=list(self.pixelFormats.keys()),
                                                editable=True)

        self.__format = self.pixelFormats["Grayscale"]
        super().__init__(name, deviceID, parameters, sensorShape)
    
    def setAcquisitionStatus(self, started: bool) -> None:
        pass
    
    def grabFrame(self) -> np.ndarray:
        # acquire image: num is the image number
        # get raw image
        raw_image = self.cam.data_stream[0].get_image()
    
        # create numpy array with data from raw image
        numpy_image = raw_image.get_numpy_array()
        if numpy_image is None:
            print("No frame available..")
            return
    
        return numpy_image
    
    def changeParameter(self, name: str, value: Any) -> None:
        if name == "Exposure time":
            value = (self.msExposure[value] if platform.startswith("win") else value)
            print("Exposuretime: "+str(value))
            self.cam.ExposureTime.set(value*1000)
        elif name == "Gain":
            value = (self.Gain[value] if platform.startswith("win") else value)
            self.cam.Gain.set(value)
        elif name == "Pixel format":
            pass #self.__format = self.pixelFormats[value]
        else:
            raise ValueError(f"Unrecognized value \"{value}\" for parameter \"{name}\"")
    
    def changeROI(self, newROI: ROI):
        return
        if newROI <= self.fullShape:
            self.roiShape = newROI
    
    def close(self) -> None:
        # stop data acquisition
        self.cam.stream_off()

        # close device
        self.cam.close_device()
