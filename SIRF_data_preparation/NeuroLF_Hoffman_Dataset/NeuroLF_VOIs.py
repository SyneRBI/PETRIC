# %%
import os
from pathlib import Path

import matplotlib.pyplot as plt
from scipy.ndimage import binary_erosion

import sirf.STIR as STIR
from petric import SRCDIR
from SIRF_data_preparation import data_QC

# %%
# %matplotlib ipympl
# %%
STIR.AcquisitionData.set_storage_scheme('memory')
# set-up redirection of STIR messages to files
# _ = STIR.MessageRedirector('BSREM_info.txt', 'BSREM_warnings.txt', 'BSREM_errors.txt')
# fewer messages from STIR and SIRF (set to higher value to diagnose have problems)
STIR.set_verbosity(0)


# %%
def plot_image(image, vmin=0, vmax=None):
    if vmax is None:
        vmax = image.max()
    plt.figure()
    plt.subplot(131)
    plt.imshow(image.as_array()[im_slice, :, :], vmin=vmin, vmax=vmax)
    plt.subplot(132)
    plt.imshow(image.as_array()[:, cor_slice, :], vmin=vmin, vmax=vmax)
    plt.subplot(133)
    plt.imshow(image.as_array()[:, :, sag_slice], vmin=vmin, vmax=vmax)
    plt.show()


# %% read
if not SRCDIR.is_dir():
    PETRICDIR = Path('~/devel/PETRIC').expanduser()
    SRCDIR = PETRICDIR / 'data'
datadir = str(SRCDIR / 'NeuroLF_Hoffman_Dataset') + '/'

# %%
OSEM_image = STIR.ImageData(datadir + 'OSEM_image.hv')
im_slice = 72
cor_slice = OSEM_image.dimensions()[1] // 2
sag_slice = OSEM_image.dimensions()[2] // 2
cmax = OSEM_image.max()

# %%
reference_image = STIR.ImageData(datadir + 'reference_image.hv')
# %% read in original VOIs
whole_object_mask = STIR.ImageData(datadir + 'whole_phantom.hv')
# whole_object_mask = STIR.ImageData(datadir+'VOI_whole_object.hv')
# from README.md
# 1: ventricles, 2: white matter, 3: grey matter
allVOIs = STIR.ImageData(datadir + 'vois_ventricles_white_grey.hv')
# %% create PETRIC VOIs
background_mask = whole_object_mask.clone()
background_mask.fill(binary_erosion(allVOIs.as_array() == 2, iterations=2))
VOI1_mask = whole_object_mask.clone()
VOI1_mask.fill(allVOIs.as_array() == 1)
VOI2_mask = whole_object_mask.clone()
VOI2_mask.fill(binary_erosion(allVOIs.as_array() == 2, iterations=1))
VOI3_mask = whole_object_mask.clone()
VOI3_mask.fill(allVOIs.as_array() == 3)
# %% write PETRIC VOIs
whole_object_mask.write(datadir + 'PETRIC/VOI_whole_object.hv')
background_mask.write(datadir + 'PETRIC/VOI_background.hv')
VOI1_mask.write(datadir + 'PETRIC/VOI_ventricles.hv')
VOI2_mask.write(datadir + 'PETRIC/VOI_WM.hv')
VOI3_mask.write(datadir + 'PETRIC/VOI_GM.hv')
# %%
VOIs = (whole_object_mask, background_mask, VOI1_mask, VOI2_mask, VOI3_mask)
# %%
[plot_image(VOI) for VOI in VOIs]
# %%
[plot_image(VOI) for VOI in VOIs]


# %%
def VOI_mean(image, VOI):
    return float((image * VOI).sum() / VOI.sum())


# %%
[VOI_mean(OSEM_image, VOI) for VOI in VOIs]
# %%
[VOI_mean(reference_image, VOI) for VOI in VOIs]

# %%
os.chdir(datadir)
# %%
data_QC.main()
# %%
voidir = Path(datadir) / 'PETRIC'
[str(voi)[:-3] for voi in voidir.glob("VOI_*.hv")]
# %%
