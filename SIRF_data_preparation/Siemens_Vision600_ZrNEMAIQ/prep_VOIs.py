# %%
# %load_ext autoreload
# %%
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_erosion

import sirf.STIR as STIR
from SIRF_data_preparation import data_QC
from SIRF_data_preparation.data_utilities import the_data_path, the_orgdata_path
from SIRF_data_preparation.dataset_settings import get_settings

# %%
# %autoreload 2

# %%
# set-up redirection of STIR messages to files
# _ = STIR.MessageRedirector('BSREM_info.txt', 'BSREM_warnings.txt', 'BSREM_errors.txt')
# fewer messages from STIR and SIRF (set to higher value to diagnose have problems)
STIR.set_verbosity(0)

# %% read
scanID = 'Siemens_Vision600_ZrNEMAIQ'
datadir = Path(the_data_path(scanID))
intermediate_datadir = Path(the_orgdata_path(scanID, 'processing'))
settings = get_settings(scanID)
slices = settings.slices
# %%
OSEM_image = STIR.ImageData(str(datadir / 'OSEM_image.hv'))
cmax = np.percentile(OSEM_image.as_array(), 99) / .99
# %% read in original VOIs
orgVOIs = []
for i in range(1, 8):
    orgVOIs.append(STIR.ImageData(str(intermediate_datadir / f"S{i}.hv")))
    data_QC.plot_image(orgVOIs[i - 1], **slices)
# %%
reference_image = STIR.ImageData(str(datadir / 'PETRIC' / 'reference_image.hv'))
data_QC.plot_image(reference_image, **slices)
# %% create PETRIC VOIs
whole_object_mask = reference_image.clone()
ref_arr = reference_image.as_array()
whole_object_mask.fill(binary_erosion(ref_arr > np.percentile(ref_arr, 5), iterations=2))
data_QC.plot_image(whole_object_mask, **slices)
# %%
background_mask = orgVOIs[6]
VOI1_mask = orgVOIs[4]
VOI2_mask = orgVOIs[2]
VOI3_mask = orgVOIs[1]
# %% write PETRIC VOIs
whole_object_mask.write(str(datadir / 'PETRIC' / 'VOI_whole_object.hv'))
VOI1_mask.write(str(datadir / 'PETRIC' / 'VOI_sphere5.hv'))
VOI2_mask.write(str(datadir / 'PETRIC' / 'VOI_sphere3.hv'))
VOI3_mask.write(str(datadir / 'PETRIC' / 'VOI_sphere2.hv'))
# %% This is the NEMA with "lung" so need to move background somewhere else
# will use the largest sphere VOI and shift it down
background_mask = orgVOIs[5].clone()
background_arr = background_mask.as_array()
z_size = background_arr.shape[0]
background_arr = np.concatenate((
    background_arr[0:35, :, :] * 0,
    background_arr[0:-35, :, :],
))
background_mask.fill(background_arr)
background_mask.write(str(datadir / 'PETRIC' / 'VOI_background.hv'))

# %%
VOInames = ('VOI_whole_object', 'VOI_background', 'VOI_sphere5', 'VOI_sphere3', 'VOI_sphere2')
data_QC.VOI_checks(VOInames, OSEM_image=OSEM_image, reference_image=reference_image, srcdir=str(datadir / 'PETRIC'))
