# %% Description
# We use  the Siemens mMR ACR VOIs from Pawel, as they match this phantom.
# However, the phantom is scanned in a different position, and reg_aladin does not
# figure it out, so we have to help it by doing manual repositioning first.

# %%
import os

import matplotlib.pyplot as plt
import numpy as np

import sirf.Reg as Reg
import sirf.STIR as STIR
from SIRF_data_preparation.data_utilities import the_data_path, the_orgdata_path
from SIRF_data_preparation.registration_utilities import STIR_to_nii, nii_to_STIR, register_it, resample_STIR

# %% set paths filenames
scanID = 'NeuroLF_Esser_Dataset'
intermediate_data_path = the_orgdata_path(scanID, 'processing')
orgdata_path = the_orgdata_path(scanID, scanID)
os.makedirs(intermediate_data_path, exist_ok=True)
data_path = the_data_path(scanID)
os.makedirs(data_path, exist_ok=True)
out_path = the_data_path(scanID, 'PETRIC')
os.makedirs(out_path, exist_ok=True)
mumap_filename = the_orgdata_path('Siemens_mMR_ACR', 'ACR_data_design/synth_mumap/acr-complete-umap.nii.gz')
mMR_data_path = the_data_path('Siemens_mMR_ACR')

# %% write current OSEM image as Nifti
OSEM_image = STIR.ImageData(os.path.join(data_path, 'OSEM_image.hv'))
OSEM_image_filename_nii = os.path.join(intermediate_data_path, 'OSEM_image.nii')
OSEM_image_nii = STIR_to_nii(OSEM_image, OSEM_image_filename_nii)
# %%
mMR_OSEM_image = STIR.ImageData(os.path.join(mMR_data_path, 'OSEM_image.hv'))
mMR_OSEM_image_filename_nii = os.path.join(intermediate_data_path, 'mMR_OSEM_image.nii')
mMR_OSEM_image_nii = STIR_to_nii(mMR_OSEM_image, mMR_OSEM_image_filename_nii)
# %% do a rotation over 180 degrees around the x-axis to get the phantom roughly in the correct place
mMR_OSEM_image_nii_rot = Reg.ImageData(mMR_OSEM_image_nii)
mMR_OSEM_image_nii_rot.fill(np.flip(mMR_OSEM_image_nii.as_array(), axis=(1, 2)))
mMR_OSEM_image_nii_rot.write(os.path.join(intermediate_data_path, 'mMR_OSEM_image_rot.nii'))
# %% do a rotation over 45 degrees around the z-axis to align the features
alpha = 45 / 180. * np.pi
m = Reg.AffineTransformation(
    np.array(((np.cos(alpha), np.sin(alpha), 0, 0), (-np.sin(alpha), np.cos(alpha), 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))))
init_resampler = Reg.NiftyResampler()
init_resampler.add_transformation(m)
init_resampler.set_interpolation_type_to_nearest_neighbour()
init_resampler.set_reference_image(mMR_OSEM_image_nii)
init_resampler.set_floating_image(mMR_OSEM_image_nii)
# %%
mMR_OSEM_image_nii_rotrot = init_resampler.forward(mMR_OSEM_image_nii_rot)
mMR_OSEM_image_nii_rotrot.write(os.path.join(intermediate_data_path, 'mMR_OSEM_image_rotrot.nii'))
# %%
plt.subplot(131)
plt.imshow(mMR_OSEM_image_nii_rot.as_array()[:, :, 20])
plt.subplot(132)
plt.imshow(mMR_OSEM_image_nii_rotrot.as_array()[:, :, 20])
plt.subplot(133)
plt.imshow(OSEM_image_nii.as_array()[:, :, 20])
# %% register
(reg_mMR_nii, resampler, reg) = register_it(OSEM_image_nii, mMR_OSEM_image_nii_rotrot)

# %% write
reg_mMR_filename = os.path.join(intermediate_data_path, 'reg_mMR')
reg_mMR = nii_to_STIR(reg_mMR_nii, reg_mMR_filename)

# %%
VOI_names = ['VOI_whole_object', 'VOI_background', 'VOI_cold_cylinder', 'VOI_hot_cylinder', 'VOI_rods']
for VOI in VOI_names:
    mMR_VOI = STIR.ImageData(os.path.join(mMR_data_path, 'PETRIC', VOI + '.hv'))
    mMR_VOI_nii = STIR_to_nii(mMR_VOI, os.path.join(intermediate_data_path, 'mMR_' + VOI + '.nii'))
    mMR_VOI_nii_rot = Reg.ImageData(mMR_VOI_nii)
    mMR_VOI_nii_rot.fill(np.flip(mMR_VOI_nii.as_array(), axis=(1, 2)))
    mMR_VOI_nii_rotrot = init_resampler.forward(mMR_VOI_nii_rot)
    VOI_im = resample_STIR(resampler, mMR_VOI_nii_rotrot, os.path.join(intermediate_data_path, VOI))
    VOI_im.write(os.path.join(out_path, VOI + '.hv'))
