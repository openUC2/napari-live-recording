import napari
from skimage.data import astronaut

import napari

napari.gui_qt()

viewer = napari.Viewer()

# create the viewer and display the image
viewer.add_image(astronaut(), rgb=True)
input()