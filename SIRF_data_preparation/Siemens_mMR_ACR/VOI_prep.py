# %% file to prepare VOIs from the original ACR NEMA VOIs supplied by Pawel Markiewicz
# %%
import os

import matplotlib.pyplot as plt
import numpy as np

import sirf.STIR as STIR
import SIRF_data_preparation.data_QC as data_QC
from SIRF_data_preparation.data_utilities import the_data_path, the_orgdata_path
from SIRF_data_preparation.dataset_settings import get_settings

# %%
scanID = 'Siemens_mMR_ACR'
org_VOI_path = the_orgdata_path(scanID, 'output', 'sampling_masks')
data_path = the_data_path(scanID)
output_path = the_data_path(scanID, 'PETRIC')
os.makedirs(output_path, exist_ok=True)
settings = get_settings(scanID)
slices = settings.slices
# %%
OSEM_image = STIR.ImageData(os.path.join(data_path, 'OSEM_image.hv'))
cmax = OSEM_image.max()
# %% read in original VOIs
orgVOIs = STIR.ImageData(os.path.join(org_VOI_path, 'acr-all-sampling-0-2mm_dipy.nii'))
data_QC.plot_image(orgVOIs, **slices)
# %%
orgVOIs_arr = orgVOIs.as_array()
print(np.unique(orgVOIs_arr))


# %% output
# [  0,  10-29,  40-81,  90- 101, 300- 317]
# %%
def plotMask(mask):
    plt.figure()
    plt.subplot(141)
    plt.imshow(mask[:, 109, :])
    plt.subplot(142)
    plt.imshow(mask[85, :, :])
    plt.subplot(143)
    plt.imshow(mask[99, :, :])
    plt.subplot(144)
    plt.imshow(mask[40, :, :])


# %% background mask: slices in uniform part (idx 300-317), taking slightly eroded mask
mask = (orgVOIs_arr >= 300) * (orgVOIs_arr < 316)
plotMask(mask)
# %%
background_mask = OSEM_image.clone()
background_mask.fill(mask)
# %% 6 cylinder masks
mask = (orgVOIs_arr >= 10) * (orgVOIs_arr < 101)
plotMask(mask)
# %% cold cylinder mask
mask = (orgVOIs_arr >= 90) * (orgVOIs_arr < 100)
plotMask(mask)
cold_cyl_mask = OSEM_image.clone()
cold_cyl_mask.fill(mask)
# %% faint hot cylinder mask
mask = (orgVOIs_arr >= 20) * (orgVOIs_arr < 29)
plotMask(mask)
hot_cyl_mask = OSEM_image.clone()
hot_cyl_mask.fill(mask)
# %% Jasczcak part, not available so derive from "background mask"
mask = (orgVOIs_arr >= 300) * (orgVOIs_arr < 316)
# get single cylinder from a slice in the background
oneslice = mask[85, :, :].copy()
mask[35:45, :, :] = oneslice[:, :]
mask[46:127, :, :] = False
plotMask(mask)
rods_mask = OSEM_image.clone()
rods_mask.fill(mask)
# %% whole phantom
mask = OSEM_image.as_array() > cmax / 20
plotMask(mask)
whole_object_mask = OSEM_image.clone()
whole_object_mask.fill(mask)
# %%
plotMask(OSEM_image.as_array())
# %% write PETRIC VOIs
whole_object_mask.write(os.path.join(output_path, 'VOI_whole_object.hv'))
background_mask.write(os.path.join(output_path, 'VOI_background.hv'))
cold_cyl_mask.write(os.path.join(output_path, 'VOI_cold_cylinder.hv'))
hot_cyl_mask.write(os.path.join(output_path, 'VOI_hot_cylinder.hv'))
rods_mask.write(os.path.join(output_path, 'VOI_rods.hv'))

# %%
VOIs = (whole_object_mask, background_mask, cold_cyl_mask, hot_cyl_mask, rods_mask)
# %%
[data_QC.plot_image(VOI, **slices) for VOI in VOIs]
# %%
data_QC.VOI_checks(['VOI_whole_object', 'VOI_background', 'VOI_cold_cylinder', 'VOI_hot_cylinder', 'VOI_rods'],
                   OSEM_image, srcdir=output_path, **slices)
