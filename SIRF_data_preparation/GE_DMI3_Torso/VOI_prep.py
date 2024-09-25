# %% file to prepare VOIs for the Torso phantom, using coordinates derived manually
import os
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_fill_holes

import sirf.STIR as STIR
from SIRF_data_preparation.data_utilities import the_data_path

# %%
scanID = 'GE_DMI3_Torso'
data_path = Path(the_data_path(scanID))
output_path = Path(the_data_path(scanID, 'PETRIC'))
os.makedirs(output_path, exist_ok=True)
# %%
image_filename = str(data_path / 'OSEM_image.hv')
image = STIR.ImageData(image_filename)
# %% find whole phantom VOI by thresholding/filling
threshold = image.max() * .05
im_arr = image.as_array() >= threshold
# we want to use binary_fill_holes to fill the spine and lung. However,
# that function does not fill holes connected to the boundary, so let's
# fill the boundary planes first
im_arr[0, :, :] = True
im_arr[-1, :, :] = True
im_arr = binary_fill_holes(im_arr)
# now exclude boundary
im_arr[0, :, :] = False
im_arr[-1, :, :] = False
VOI = image.allocate(0)
VOI.fill(im_arr.astype(np.float32))
VOI.show()
VOI.write(str(output_path / 'VOI_whole_object.hv'))
# %% find centre image as KT got the coordinates from Amide
# note that geo.get_index_to_physical_point_matrix() is still unstable, so we won't use it.
# Warning: the following will likely fail for future versions of SIRF
zcentre = (image.shape[0] - 1) / 2 * image.voxel_sizes()[0]
# %% background VOI (in approx middle of torso)
shape = STIR.EllipticCylinder()
shape.set_length(23)
shape.set_radii((120, 120))
shape.set_origin((zcentre + 0, 0, 0))
VOI.fill(0)
VOI.add_shape(shape, scale=1)
VOI.write(str(output_path / 'VOI_background.hv'))
# %% spine (approximately top half of it)
shape = STIR.EllipticCylinder()
shape.set_length(100)
shape.set_radii((22, 22))
shape.set_origin((zcentre + 42.6, 86.9, 3))
VOI.fill(0)
VOI.add_shape(shape, scale=1)
VOI.write(str(output_path / 'VOI_spine.hv'))
VOI.show()
# %% lung lesion
shape = STIR.Ellipsoid()
shape.set_radius_z(5)
shape.set_radius_y(5)
shape.set_radius_x(5)
shape.set_origin((zcentre + 25, -42.2, -105.3))
VOI.fill(0)
VOI.add_shape(shape, scale=1)
VOI.write(str(output_path / 'VOI_lung_lesion.hv'))
# %%
# %% liver lesion
shape = STIR.Ellipsoid()
shape.set_radius_z(5)
shape.set_radius_y(5)
shape.set_radius_x(5)
shape.set_origin((zcentre - 38.2, -38.9, -49.7))
VOI.fill(0)
VOI.add_shape(shape, scale=1)
VOI.write(str(output_path / 'VOI_liver_lesion.hv'))
# %% lung lesion
shape = STIR.Ellipsoid()
shape.set_radius_z(5)
shape.set_radius_y(5)
shape.set_radius_x(5)
shape.set_origin((zcentre + 47.6, 12.5, 151.5))
VOI.fill(0)
VOI.add_shape(shape, scale=1)
VOI.write(str(output_path / 'VOI_chest_lesion.hv'))
